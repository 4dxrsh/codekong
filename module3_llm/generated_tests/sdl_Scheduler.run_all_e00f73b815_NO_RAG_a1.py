from schedule.__init__ import Scheduler

def test_run_all_logs_job_count_and_delay():
    scheduler = Scheduler()
    job1 = make_mock_job("job1")
    job2 = make_mock_job("job2")
    scheduler.jobs.extend([job1, job2])

    with mock.patch('schedule.logger.debug') as mock_debug:
        scheduler.run_all(delay_seconds=5)

    expected_message = "Running *all* 2 jobs with 5s delay in between"
    assert mock_debug.call_args_list[0][0][0] == expected_message