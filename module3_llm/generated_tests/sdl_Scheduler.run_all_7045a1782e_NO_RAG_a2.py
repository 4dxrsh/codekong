from schedule.__init__ import Scheduler

def test_run_all_with_delay():
    scheduler = Scheduler()
    job = mock.Mock()
    scheduler.jobs.append(job)
    
    with mock_datetime(2023, 10, 1, 12, 0):
        scheduler.run_all(delay_seconds=5)
    
    assert job._run_job.call_count == len(scheduler.jobs), "All jobs should be run"
    assert job._run_job.call_args_list[0][0] == (job,), "First job should be passed correctly"
    assert job._run_job.call_args_list[1][0] == (job,), "Second job should be passed correctly"
    assert job._run_job.call_args_list[2][0] == (job,), "Third job should be passed correctly"