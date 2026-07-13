from schedule.__init__ import Job

def test_job_run_logs_running():
    job = Job()
    job.job_func = mock.Mock(return_value="result")
    
    with mock.patch('schedule.logger.debug') as mock_debug:
        result = job.run()
    
    assert result == "result"
    mock_debug.assert_called_once_with("Running job %s", job)