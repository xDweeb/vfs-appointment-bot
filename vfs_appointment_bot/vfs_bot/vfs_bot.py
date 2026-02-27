import argparse
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List

import playwright
from playwright.sync_api import sync_playwright

from vfs_appointment_bot.utils.config_reader import get_config_value
from vfs_appointment_bot.notification.notification_client_factory import (
    get_notification_client,
)


def _apply_stealth(page):
    """Apply stealth to a page, compatible with playwright-stealth v1 and v2."""
    try:
        from playwright_stealth import Stealth
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
    except (ImportError, TypeError, AttributeError):
        try:
            from playwright_stealth import stealth_sync
            stealth_sync(page)
        except ImportError:
            logging.warning("playwright-stealth not available, continuing without stealth")


class LoginError(Exception):
    """Exception raised when login fails."""


class VfsBot(ABC):
    """
    Abstract base class for VfsBot

    Provides common functionalities like login, pre-login steps, appointment checking, and notification.
    Subclasses are responsible for implementing country-specific login and appointment checking logic.
    """

    def __init__(self):
        """
        Initializes a VfsBot instance for a specific country.

        """
        self.source_country_code = None
        self.destination_country_code = None
        self.appointment_param_keys: List[str] = []

    def run(self, args: argparse.Namespace = None) -> bool:
        """
        Starts the VFS bot for appointment checking and notification.

        This method reads configuration values, performs login, checks for
        appointments based on provided arguments, and sends notifications if
        appointments are found.

        Args:
            args (argparse.Namespace, optional): Namespace object containing parsed
                command-line arguments. Defaults to None.

        Returns:
            bool: True if appointments were found, False otherwise.
        """

        country_pair = f"{self.source_country_code.upper()}-{self.destination_country_code.upper()}"
        logging.info(f"Starting VFS Bot for {country_pair}")

        # Configuration values
        try:
            browser_type = get_config_value("browser", "type", "chromium")
            headless_mode = get_config_value("browser", "headless", "true")
            url_key = self.source_country_code + "-" + self.destination_country_code
            vfs_url = get_config_value("vfs-url", url_key)
            if not vfs_url:
                logging.error(f"No VFS URL configured for {url_key}")
                return False
        except KeyError as e:
            logging.error(f"Missing configuration value: {e}")
            return False

        email_id = get_config_value("vfs-credential", "email")
        password = get_config_value("vfs-credential", "password")

        appointment_params = self.get_appointment_params(args)

        # Launch browser and perform actions
        logging.info(f"Launching {browser_type} browser (headless={headless_mode})")
        start_time = time.time()

        with sync_playwright() as p:
            browser = getattr(p, browser_type).launch(
                headless=headless_mode.lower() in ("true", "1", "yes")
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            page = context.new_page()
            _apply_stealth(page)

            logging.info(f"Navigating to VFS: {vfs_url}")
            page.goto(vfs_url, wait_until="networkidle", timeout=60000)
            self.pre_login_steps(page)

            try:
                logging.info("Attempting login...")
                self.login(page, email_id, password)
                login_time = time.time() - start_time
                logging.info(f"Logged in successfully (took {login_time:.1f}s)")
            except Exception as e:
                browser.close()
                raise LoginError(
                    f"Login failed: {e}. "
                    "Please verify your username and password."
                )

            logging.info(f"Checking appointments for {appointment_params}")
            appointment_found = False
            try:
                dates = self.check_for_appointment(page, appointment_params)
                check_time = time.time() - start_time
                if dates:
                    logging.info(
                        f"FOUND appointments on: {', '.join(dates)} (total time: {check_time:.1f}s)"
                    )
                    self.notify_appointment(appointment_params, dates)
                    appointment_found = True
                else:
                    logging.info(
                        f"No appointments found. (checked in {check_time:.1f}s)"
                    )
            except Exception as e:
                logging.error(f"Appointment check failed: {e}")
            browser.close()
            return appointment_found

    def get_appointment_params(self, args: argparse.Namespace) -> Dict[str, str]:
        """
        Collects appointment parameters from command-line arguments or user input.

        This method iterates through pre-defined `appointment_param_keys` (replace
        with relevant keys) and retrieves values either from provided arguments
        or prompts the user for input if values are missing.

        Args:
            args (argparse.Namespace): Namespace object containing parsed command-line arguments.

        Returns:
            Dict[str, str]: A dictionary containing appointment parameters.
        """
        appointment_params = {}
        args_params = getattr(args, "appointment_params", None) or {}
        for key in self.appointment_param_keys:
            if key in args_params and args_params[key] is not None:
                appointment_params[key] = args_params[key]
            else:
                key_name = key.replace("_", " ")
                appointment_params[key] = input(f"Enter the {key_name}: ")
        return appointment_params

    def notify_appointment(self, appointment_params: Dict[str, str], dates: List[str]):
        """
        Sends appointment dates notification to the user.

        This method is responsible for notifying the appointment dates to the user configured channels

        Args:
            dates (List[str]): A list of appointment dates.
            appointment_params (Dict[str, str]): A dictionary containing appointment search criteria.
        """
        message = f"Found appointment(s) for {', '.join(appointment_params.values())} on {', '.join(dates)}"
        channels = get_config_value("notification", "channels", "")
        if not channels or len(channels.strip()) == 0:
            logging.warning(
                "No notification channels configured. Skipping notification."
            )
            return

        for channel in channels.split(","):
            channel = channel.strip()
            if not channel:
                continue
            client = get_notification_client(channel)
            try:
                client.send_notification(message)
            except Exception:
                logging.error(f"Failed to send {channel} notification")

    @abstractmethod
    def login(
        self, page: playwright.sync_api.Page, email_id: str, password: str
    ) -> None:
        raise NotImplementedError("Subclasses must implement login logic")

    @abstractmethod
    def pre_login_steps(self, page: playwright.sync_api.Page) -> None:
        pass

    @abstractmethod
    def check_for_appointment(
        self, page: playwright.sync_api.Page, appointment_params: Dict[str, str]
    ) -> List[str]:
        raise NotImplementedError(
            "Subclasses must implement appointment checking logic"
        )
