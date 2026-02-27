import logging
from typing import Dict, List, Optional

from playwright.sync_api import Page

from vfs_appointment_bot.utils.date_utils import extract_date_from_string
from vfs_appointment_bot.vfs_bot.vfs_bot import VfsBot


class VfsBotSchengen(VfsBot):
    """VFS Bot for Schengen countries (Portugal, Spain, etc.).

    Handles login, cookie rejection, and appointment checking for
    Schengen visa appointments on VFS Global.
    """

    def __init__(self, source_country_code: str, destination_country_code: str):
        super().__init__()
        self.source_country_code = source_country_code
        self.destination_country_code = destination_country_code.upper()
        self.appointment_param_keys = [
            "visa_center",
            "visa_category",
            "visa_sub_category",
        ]

    def login(self, page: Page, email_id: str, password: str) -> None:
        """Login to VFS Global for Schengen countries."""
        # Wait for the login form to be ready
        page.wait_for_selector("#mat-input-0", timeout=30000)

        email_input = page.locator("#mat-input-0")
        password_input = page.locator("#mat-input-1")

        email_input.fill(email_id)
        password_input.fill(password)

        page.get_by_role("button", name="Sign In").click()

        # Wait for successful login - look for the booking button
        page.wait_for_selector(
            "role=button >> text=Start New Booking", timeout=30000
        )

    def pre_login_steps(self, page: Page) -> None:
        """Handle cookie consent and other pre-login popups."""
        try:
            # Try different cookie rejection button texts
            for button_text in ["Reject All", "Reject all", "Decline", "Tout refuser"]:
                reject_btn = page.get_by_role("button", name=button_text)
                if reject_btn.count() > 0:
                    reject_btn.first.click()
                    logging.debug(f"Clicked '{button_text}' cookie button")
                    page.wait_for_timeout(1000)
                    return
            logging.debug("No cookie consent button found, continuing")
        except Exception:
            logging.debug("Cookie handling skipped, continuing")

    def check_for_appointment(
        self, page: Page, appointment_params: Dict[str, str]
    ) -> Optional[List[str]]:
        """Check for available Schengen visa appointments."""
        page.get_by_role("button", name="Start New Booking").click()

        # Select Visa Centre
        visa_centre_dropdown = page.wait_for_selector(
            "mat-form-field", timeout=15000
        )
        visa_centre_dropdown.click()
        visa_centre_option = page.wait_for_selector(
            f'mat-option:has-text("{appointment_params.get("visa_center")}")',
            timeout=10000,
        )
        visa_centre_option.click()
        page.wait_for_timeout(1000)

        # Select Visa Category
        visa_category_dropdown = page.query_selector_all("mat-form-field")[1]
        visa_category_dropdown.click()
        visa_category_option = page.wait_for_selector(
            f'mat-option:has-text("{appointment_params.get("visa_category")}")',
            timeout=10000,
        )
        visa_category_option.click()
        page.wait_for_timeout(1000)

        # Select Subcategory
        visa_subcategory_dropdown = page.query_selector_all("mat-form-field")[2]
        visa_subcategory_dropdown.click()
        visa_subcategory_option = page.wait_for_selector(
            f'mat-option:has-text("{appointment_params.get("visa_sub_category")}")',
            timeout=10000,
        )
        visa_subcategory_option.click()
        page.wait_for_timeout(2000)

        # Check for appointment dates
        try:
            page.wait_for_selector("div.alert", timeout=10000)
            appointment_date_elements = page.query_selector_all("div.alert")
            appointment_dates = []
            for element in appointment_date_elements:
                text = element.text_content()
                date = extract_date_from_string(text)
                if date is not None and len(date) > 0:
                    appointment_dates.append(date)
            return appointment_dates if appointment_dates else None
        except Exception:
            return None
