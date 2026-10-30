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


def split_delivery_fee(total_fee_cents: int, member_ids: list[int]):
    if not member_ids:
        raise ValueError("Cannot split fee without members.")
    if total_fee_cents < 0:
        raise ValueError("Delivery fee cannot be neagtive.") # ErrorChecking in general, for us our fee is 1595.
    sorted_ids = sorted(member_ids) # Sort ids to make rounding deviations. 
    base_share = total_fee_cents// len(sorted_ids) # Same base amount for everyone involved.
    remainder = total_fee_cents % len(sorted_ids)
    shares = {}
    for index, member_id in enumerate(sorted_ids):
        shares[member_id] = base_share
        if index < remainder:
            shares[member_id] += 1
    return shares
