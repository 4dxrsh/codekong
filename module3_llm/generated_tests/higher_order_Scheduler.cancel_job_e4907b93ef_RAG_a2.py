from schedule.__init__ import Scheduler

def test_cancel_job_correct():
    scheduler = Scheduler()
    job = mock.Mock()
    scheduler.jobs.append(job)
    scheduler.cancel_job(job)
    assert job not in scheduler.jobs, "Job was not removed from the scheduler"

def test_cancel_job_missing_debug_statements():
    scheduler = Scheduler()
    job = mock.Mock()
    scheduler.jobs.append(job)
    with mock.patch('schedule.logger.debug') as debug_mock:
        scheduler.cancel_job(job)
        debug_mock.assert_any_call('Cancelling job "%s"', str(job))
        debug_mock.assert_any_call('Cancelling not-scheduled job "%s"', str(job))

def test_cancel_job_missing_debug_statements_separately():
    scheduler = Scheduler()
    job = mock.Mock()
    scheduler.jobs.append(job)
    
    with mock.patch('schedule.logger.debug', side_effect=['Cancelling job "%s"', 'Cancelling not-scheduled job "%s"']) as debug_mock:
        scheduler.cancel_job(job)
        assert debug_mock.call_args_list[0][0][1] == str(job), "First debug statement is missing"
    
    with mock.patch('schedule.logger.debug', side_effect=['Cancelling not-scheduled job "%s"', 'Cancelling job "%s"']) as debug_mock:
        scheduler.cancel_job(job)
        assert debug_mock.call_args_list[0][0][1] == str(job), "Second debug statement is missing"