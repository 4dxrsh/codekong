from schedule.__init__ import Scheduler

def test_run_all_logs_job_count_and_delay():
    scheduler = Scheduler()
    job1 = mock.Mock()
    job2 = mock.Mock()
    scheduler.jobs.extend([job1, job2])

    with mock.patch('schedule.logger.debug') as mock_debug:
        scheduler.run_all(delay_seconds=5)

    assert mock_debug.call_args_list == [
        mock.call("Running *all* 2 jobs with 5s delay in between"),
        mock.call("Running job %s", job1),
        mock.call("Running job %s", job2)
    ]