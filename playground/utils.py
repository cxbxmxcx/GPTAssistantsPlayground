import uuid


def id_to_uuid(custom_id):
    # Ensure the custom ID is 32 characters long for UUID (128 bits)
    # If shorter, pad with zeros; if longer, truncate
    padded_id = (custom_id + "0" * 32)[:32]

    # Convert to bytes
    byte_sequence = padded_id.encode("utf-8")

    # Create a UUID from the bytes
    generated_uuid = uuid.UUID(bytes=byte_sequence[:16])

    return generated_uuid
