from schedule.__init__ import Job

def test_job_run_logs_running():
    job = Job()
    job.job_func = mock.Mock(return_value="result")
    
    with mock_datetime(2023, 10, 1, 12, 0):
        result = job.run()
    
    assert result == "result"
    assert job.last_run == datetime.datetime(2023, 10, 1, 12, 0)
    assert job._schedule_next_run.call_count == 1