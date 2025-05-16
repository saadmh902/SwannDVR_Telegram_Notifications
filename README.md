# SwannDVR_Telegram_Notifications
SwannDVR notifications don't have previews, this uses the built in email notification function, strips the image and sends it to your phone using Telegram and gives you a preview of the motion that was detected

Running example on iPhone lockscreen:

<img width="429" alt="example" src="https://github.com/user-attachments/assets/7249e38b-3b11-4c27-816d-12bcdee7e77b" />


Multiple people can receive these notifications

<img width="338" alt="Untitled" src="https://github.com/user-attachments/assets/596c21b8-0ccc-4758-bb2d-7cf13c324e59" />


Installation Instructions:

1. Message Botfather on Telegram and create a new bot, get the API key and your chat ID with the bot
2.  Edit run.py and add the IP of the machine you will be running this on, as well as your chat ID and API key
3.  Open SwannDVR, go to Alarms -> Email Notifications, set these options:
     Email = Enabled
     Encryption = Disable
     SMTP Port = 1025
     SMTP Server = (IP address of the machine running run.py)
     Username = 123
     Password = 123
     Sender = Anything you want
     Receiver1 Receiver2 Receiver3 = Anything you want
     Interval 1Min
4. Click Test email, it should send you a Telegram notification
5. Click Save

   All done!
   
