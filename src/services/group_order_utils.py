import secrets
import hashlib # For hashing purposes, like creating secure share codes!

def generate_share_code(length = 8):
    #Excluding ambiguous characters  like 0, O, I and 1.
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" # Excluding 0, O, I, and 1 to avoid confusion.
    return ''.join(secrets.choice(alphabet) for _ in range(length))
def generate_member_credential(): # Generates unpredictable member credentials.
    return secrets.token_urlsafe(32)
def hash_credential(credential): #Stores hash instead of the original credentials.
    return hashlib.sha256(credential.encode("utf-8)")).hexdigest()

