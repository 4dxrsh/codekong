from schedule.__init__ import repeat

def test_repeat_decorator():
    job = mock.Mock()
    
    @repeat(job)
    def my_function():
        pass
    
    assert job.do.call_count == 1
    assert job.do.call_args[0][0] is my_function