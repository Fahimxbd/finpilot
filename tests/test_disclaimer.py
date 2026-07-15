from core.disclaimer import MASTER_DISCLAIMER, TRADING_DISCLAIMER, attach_disclaimer, disclaimed


def test_attach_disclaimer_wraps_payload() -> None:
    output = attach_disclaimer({"value": 3})
    assert output["data"] == {"value": 3}
    assert output["disclaimer"] == MASTER_DISCLAIMER


def test_trading_disclaimer_is_stricter() -> None:
    output = attach_disclaimer("summary", context="trading")
    assert MASTER_DISCLAIMER in output["disclaimer"]
    assert TRADING_DISCLAIMER in output["disclaimer"]


def test_decorator_always_wraps() -> None:
    @disclaimed("tax")
    def example() -> dict[str, bool]:
        return {"ok": True}

    assert example()["disclaimer"] == MASTER_DISCLAIMER
