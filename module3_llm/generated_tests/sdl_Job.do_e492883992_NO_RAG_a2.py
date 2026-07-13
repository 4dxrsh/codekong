from schedule.__init__ import Job, ScheduleError

def test_do_with_missing_scheduler():
    job = Job()
    with pytest.raises(ScheduleError) as exc_info:
        job.do(lambda: None)
    assert str(exc_info.value) == "Unable to a add job to schedule. Job is not associated with an scheduler"