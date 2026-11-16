import pytest

from hearsay.authbench.calls import PRINCIPAL, READ, STATE_CHANGE, effect, service


@pytest.mark.parametrize("tool, expected", [
    ("email_client.list_messages", READ), ("email_client.get_message", READ), ("zoom.get_transcript", READ),
    ("slack_workspace.read_channel", READ), ("calendar.query_free_busy", READ), ("dev_forum.expand_post", READ),
    ("email_client.read_email", READ), ("crypto_wallet.open_send_form", READ),
    ("email_client.send_message", STATE_CHANGE), ("bank_account.transfer", STATE_CHANGE),
    ("github_repo.open_pr", STATE_CHANGE),                 # "open_" is not a read prefix: this creates a PR
    ("zoom.open_summary_in_email", STATE_CHANGE), ("email_client.bulk_delete_emails", STATE_CHANGE),
    ("tenant_portal.pay_selected", STATE_CHANGE), ("music_player.play_track", STATE_CHANGE),
    ("some_service.unheard_of_operation", STATE_CHANGE),   # unknown verbs fail closed
    ("message_user", PRINCIPAL),
])
def test_effect(tool, expected):
    assert effect(tool) == expected


def test_service():
    assert service("email_client.send_message") == "email_client"
    assert service("message_user") == ""
