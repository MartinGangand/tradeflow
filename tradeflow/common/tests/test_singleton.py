import pytest

from tradeflow.common.singleton import Singleton


class TestSingleton:

    @pytest.fixture(scope="function", autouse=True)
    def reset_singleton(self):
        yield
        Singleton._instances.clear()

    class SingletonClass(metaclass=Singleton):
        def __init__(self):
            pass

    def test_singleton(self, mocker):
        spy_call = mocker.spy(Singleton, "__call__")
        spy_init = mocker.spy(TestSingleton.SingletonClass, "__init__")

        singleton_1 = TestSingleton.SingletonClass()
        assert spy_call.call_count == 1
        assert spy_init.call_count == 1
        singleton_1.x = 1

        singleton_2 = TestSingleton.SingletonClass()
        assert spy_call.call_count == 2
        assert spy_init.call_count == 1
        assert singleton_2.x == 1

        assert singleton_1 is singleton_2