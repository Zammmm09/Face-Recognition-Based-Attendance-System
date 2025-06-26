from twilio.rest import Client

# Twilio credentials
account_sid = 'AC9717e23a8b6a334f668fc0728dc6ed66'  # Your Account SID
auth_token = 'cd7d11d79d0153dceca774b6fa759629'    # Your Auth Token
twilio_sms_number = '+13072125079'                 # Your Twilio SMS number

# Initialize Twilio client
client = Client(account_sid, auth_token)

def send_sms_notification(to_number, message):
    """
    Send an SMS notification to a specific number.
    :param to_number: Recipient's phone number (e.g., '+918308553555')
    :param message: Message to send
    """
    try:
        message = client.messages.create(
            body=message,
            from_=twilio_sms_number,
            to=to_number
        )
        print(f"✅ SMS notification sent to {to_number}: {message.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS notification: {e}")

# Example usage
student_name = "Asha Pathan"
attendance_status = "Present"
recipient_number = "+918308553555"  # Recipient's phone number

message = f"Attendance Update: {student_name} is marked {attendance_status}."
send_sms_notification(recipient_number, message)