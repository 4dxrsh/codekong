from schedule.__init__ import repeat

def test_repeat_decorator():
    mock_job = mock.Mock()
    
    @repeat(mock_job)
    def job_fun():
        pass
    
    assert mock_job.do.called_once_with(job_fun, (), {})