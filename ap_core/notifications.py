"""
Desktop notifications for download completion
"""
import sys
import subprocess


def notify(title: str, message: str, urgency: str = "normal"):
    """
    Send desktop notification
    
    Args:
        title: Notification title
        message: Notification body
        urgency: low, normal, or critical
    """
    platform = sys.platform.lower()
    
    try:
        if platform == "linux":
            _notify_linux(title, message, urgency)
        elif platform == "darwin":
            _notify_macos(title, message)
        elif platform == "win32":
            _notify_windows(title, message)
    except Exception:
        # Fail silently if notifications unavailable
        pass


def _notify_linux(title: str, message: str, urgency: str):
    """Linux notification via notify-send"""
    try:
        subprocess.run(
            ["notify-send", "-u", urgency, title, message],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        # notify-send not installed
        pass


def _notify_macos(title: str, message: str):
    """macOS notification via osascript"""
    script = f'display notification "{message}" with title "{title}"'
    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pass


def _notify_windows(title: str, message: str):
    """Windows notification via PowerShell"""
    try:
        # Use Windows toast notification
        ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">{title}</text>
            <text id="2">{message}</text>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("AutoPahe").Show($toast)
"""
        subprocess.run(
            ["powershell", "-Command", ps_script],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


def notify_download_complete(anime_name: str, episodes: str):
    """Notify when download completes"""
    title = "AutoPahe - Download Complete"
    message = f"{anime_name} - Episodes {episodes}"
    notify(title, message, "normal")


def notify_download_failed(anime_name: str, error: str):
    """Notify when download fails"""
    title = "AutoPahe - Download Failed"
    message = f"{anime_name}: {error}"
    notify(title, message, "critical")
