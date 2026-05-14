from app import automate_google_login
import pprint

result = automate_google_login('test@gmail.com', 'dummy_password')
pprint.pprint(result)
