from tesla_lease_tracker.backend.logger import correlation_id_var, generate_correlation_id


class TestCorrelationId:
    def test_generate_returns_12_char_hex(self):
        cid = generate_correlation_id()
        assert len(cid) == 12
        assert all(c in "0123456789abcdef" for c in cid)

    def test_context_var_default_empty(self):
        assert correlation_id_var.get() == ""

    def test_context_var_set_and_get(self):
        token = correlation_id_var.set("test-123")
        assert correlation_id_var.get() == "test-123"
        correlation_id_var.reset(token)
        assert correlation_id_var.get() == ""
