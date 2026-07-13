from schedule.__init__ import Scheduler

def test_run_all_with_delay():
    scheduler = Scheduler()
    job = mock.Mock()
    scheduler.jobs.append(job)
    
    with mock_datetime(2023, 10, 1, 12, 0):
        scheduler.run_all(delay_seconds=5)
    
    assert job.call_count == len(scheduler.jobs), "All jobs should be run"
    for call_args, _ in job.call_args_list:
        assert call_args[0] == (datetime.datetime(2023, 10, 1, 12, 0),), "Job called with correct arguments"