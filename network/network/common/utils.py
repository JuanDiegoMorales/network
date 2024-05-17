class BColors:
    HEADER = '\033[95m'
    OK_BLUE = '\033[94m'
    OK_CYAN = '\033[96m'
    OK_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END_C = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def debug_exception(origin: str, message: str):
    print(f"{BColors.FAIL} | {origin} | {message} {BColors.END_C}")


def debug_warning(origin: str, message: str):
    print(f"{BColors.BOLD}{BColors.WARNING} | {origin} | {message} {BColors.END_C}")


def debug_log(origin: str, message: str):
    print(f"{BColors.OK_BLUE} | {origin} | {message} {BColors.END_C}")