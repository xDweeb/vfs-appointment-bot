from vfs_appointment_bot.vfs_bot.vfs_bot import VfsBot


class UnsupportedCountryError(Exception):
    """Raised when an unsupported country code is provided."""


# Schengen countries that share the same VFS page structure
SCHENGEN_COUNTRIES = {"PT", "ES", "FR", "NL", "BE", "AT", "CH", "CZ", "PL", "SE", "NO", "DK", "FI", "GR", "HU"}


def get_vfs_bot(source_country_code: str, destination_country_code: str) -> VfsBot:
    """Retrieves the appropriate VfsBot class for a given country pair.

    Args:
        source_country_code (str): Where you're applying from (e.g., "MA").
        destination_country_code (str): Where the appointment is (e.g., "PT", "ES").

    Returns:
        VfsBot: An instance of the appropriate VfsBot subclass.

    Raises:
        UnsupportedCountryError: If the provided country is not supported.
    """
    dest = destination_country_code.upper()

    if dest in SCHENGEN_COUNTRIES:
        from .vfs_bot_schengen import VfsBotSchengen
        return VfsBotSchengen(source_country_code, dest)
    elif dest == "DE":
        from .vfs_bot_de import VfsBotDe
        return VfsBotDe(source_country_code)
    elif dest == "IT":
        from .vfs_bot_it import VfsBotIt
        return VfsBotIt(source_country_code)
    else:
        raise UnsupportedCountryError(
            f"Country {destination_country_code} is not supported. "
            f"Supported: DE, IT, {', '.join(sorted(SCHENGEN_COUNTRIES))}"
        )
