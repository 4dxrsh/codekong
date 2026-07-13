from schedule.__init__ import Scheduler

def test_run_all_with_delay():
    scheduler = Scheduler()
    job1 = mock.Mock()
    job2 = mock.Mock()
    scheduler.jobs.extend([job1, job2])

    with mock.patch('time.sleep') as sleep_mock:
        scheduler.run_all(delay_seconds=1)

    assert job1._run_job.call_count == 1
    assert job2._run_job.call_count == 1
    assert sleep_mock.call_count == 2

def test_run_all_without_delay():
    scheduler = Scheduler()
    job1 = mock.Mock()
    job2 = mock.Mock()
    scheduler.jobs.extend([job1, job2])

    with mock.patch('time.sleep') as sleep_mock:
        scheduler.run_all(delay_seconds=0)

    assert job1._run_job.call_count == 1
    assert job2._run_job.call_count == 1
    assert sleep_mock.call_count == 0

def test_run_all_with_single_job():
    scheduler = Scheduler()
    job1 = mock.Mock()
    scheduler.jobs.append(job1)

    with mock.patch('time.sleep') as sleep_mock:
        scheduler.run_all(delay_seconds=1)

    assert job1._run_job.call_count == 1
    assert sleep_mock.call_count == 1

def test_run_all_with_no_jobs():
    scheduler = Scheduler()

    with mock.patch('time.sleep') as sleep_mock:
        scheduler.run_all(delay_seconds=1)

    assert not scheduler.jobs
    assert sleep_mock.call_count == 0