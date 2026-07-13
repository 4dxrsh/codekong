from schedule.__init__ import repeat

def test_repeat_decorator():
    job = mock.Mock()
    
    @repeat(job)
    def my_function():
        pass
    
    assert job.do.call_args_list == [mock.call(my_function)]
    assert my_function not in job.do.call_args_list[0][0]