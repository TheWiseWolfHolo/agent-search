from importlib import metadata


APP_NAME = "WolfHolo Agent Search"
CLI_NAME = "agent-search"
PACKAGE_NAME = "agent-search"
NPM_PACKAGE_NAME = "@thewisewolfholo/agent-search"
REPOSITORY = "TheWiseWolfHolo/agent-search"


def get_version() -> str:
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return "0.1.0"


def user_agent(component: str = "") -> str:
    suffix = f" {component.strip()}" if component.strip() else ""
    return f"{CLI_NAME}/{get_version()}{suffix}"

