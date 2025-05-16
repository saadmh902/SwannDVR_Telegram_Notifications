import asyncio
import base64
import os
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP
from email import message_from_bytes
from email.policy import default
from datetime import datetime
import requests
import re
#SERVER INFO:

hostname = "192.168.0.1" #CHANGE TO YOUR IP
port = 1025 #CAN STAY THE SAME 

#Telegram Info:

CHAT_IDS = ["00000000000000"] #ENTER YOUR TELEGRAM CHAT ID WITH THE BOT HERE, multiple CHAT_IDs can be added e.g. ["chatid1","chatid2"]
BOT_TOKEN = '' #Your own bot tocken

SAVE_DIR = "./camera_snapshots"
os.makedirs(SAVE_DIR, exist_ok=True)
def getEmailBody(msg):
    body = None
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors="ignore")
                    break
    else:
        charset = msg.get_content_charset() or "utf-8"
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(charset, errors="ignore")

    if body:
        body = body.strip()
        device_match = re.search(r'Device Name:\s*(.+)', body)
        channel_match = re.search(r'Channel Name:\s*(\[[^\]]+\]:\s*.+)', body)
        device_name = device_match.group(1).strip() if device_match else "Unknown Device"
        channel_name = channel_match.group(1).strip() if channel_match else "Unknown Channel"
        return f"📺 {device_name} {channel_name}"
    else:
        print("⚠️ No text/plain body found.")


def send_telegram_image(image="", CAPTION="",CHAT_ID="",BOT_TOKEN=""):
    #IMAGE_PATH = './camera_snapshots/motion_20250515_225011.jpg'  # replace with dynamic filename if needed
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    #print(url)
    with open(image, 'rb') as photo:
        response = requests.post(url, data={
            'chat_id': CHAT_ID,
            'caption': CAPTION
        }, files={'photo': photo})
    if response.status_code == 200:
        print(f"✅ Notification sent to {CHAT_ID}")
    else:
        print(f"❌ Failed to send image: {response.text}")




class CameraSMTPHandler:
    async def handle_MAIL(self, server, session, envelope, address, mail_options):
        envelope.mail_from = address
        return '250 OK'

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):
        msg = message_from_bytes(envelope.content, policy=default)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dynamic_caption = getEmailBody(msg)
        for part in msg.iter_attachments():
            filename = part.get_filename()
            if filename and part.get_content_type().startswith("image/"):
                image_path = os.path.join(SAVE_DIR, f"motion_{timestamp}.jpg")
                with open(image_path, "wb") as f:
                    f.write(part.get_content())
                #input(f"wroten image {image_path}")
                print(f"Motion Detected... Saved as {image_path}")
                for CHAT_ID in CHAT_IDS:
                    #print(CHAT_ID)
                    send_telegram_image(image=image_path, CAPTION=dynamic_caption,CHAT_ID=CHAT_ID,BOT_TOKEN=BOT_TOKEN) #Send telegram image to phone
        return '250 Message accepted for delivery'

class SilentSMTP(SMTP):
    def __init__(self, handler, *args, **kwargs):
        super().__init__(handler, *args, **kwargs)
        self._handler = handler  # ✅ fix: explicitly store handler

    async def smtp_DATA(self, *args):
        await self.push("354 End data with <CR><LF>.<CR><LF>")
        data_lines = []
        while True:
            line = await self._reader.readline()
            if line == b'.\r\n':
                break
            if line.startswith(b'..'):
                line = line[1:]
            data_lines.append(line)
        self.envelope.content = b''.join(data_lines)
        status = await self._handler.handle_DATA(self, self.session, self.envelope)
        await self.push(status)

    async def smtp_AUTH(self, arg):
        if arg.upper() == 'LOGIN':
            await self.push("334 VXNlcm5hbWU6")
            b64_username = await self.receive_data()
            await self.push("334 UGFzc3dvcmQ6")
            b64_password = await self.receive_data()
            try:
                username = base64.b64decode(b64_username).decode()
                password = base64.b64decode(b64_password).decode()
            except:
                await self.push("535 Invalid base64 encoding")
                return
            if username == "123" and password == "123":
                await self.push("235 Authentication successful")
            else:
                await self.push("535 Authentication failed")

    async def receive_data(self):
        line = await self._reader.readline()
        return line.decode().strip()

    async def handle_command(self, line):
        if not line:
            return
        line = line.strip()
        if line == ".":
            return  # ✅ suppress bare period
        else:
            print(f"'{line}'")
        parts = line.split()
        command = parts[0].upper()
        arg = " ".join(parts[1:]) if len(parts) > 1 else None
        method = getattr(self, "smtp_" + command, None)
        if method:
            await method(arg)
        else:
            await self.push("250 OK")  # ✅ quietly accept unknown

class SilentController(Controller):
    def factory(self):
        return SilentSMTP(self.handler)


controller = SilentController(CameraSMTPHandler(), hostname=hostname, port=port)
controller.start()

print(f"📡 SMTP server running on {hostname}:{str(port)}")

async def keep_alive():
    while True:
        await asyncio.sleep(1)

try:
    asyncio.run(keep_alive())
except KeyboardInterrupt:
    controller.stop()
