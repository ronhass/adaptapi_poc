def upgrade_request(body):
    body["greeting"] = "Hello"
    return body


def downgrade_response(body):
    return body
