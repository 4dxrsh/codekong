from schedule.__init__ import Job

def test_job_run_updates_last_run():
    job = Job()
    job.job_func = mock.Mock(return_value="result")
    
    with mock_datetime(2023, 10, 5, 14, 0):
        result = job.run()
    
    assert result == "result"
    assert job.last_run == datetime.datetime(2023, 10, 5, 14, 0)