from schedule.__init__ import Job

def test_tag_type_enforcement():
    job1 = every().second.do(make_mock_job(name="job1"))
    try:
        job1.tag({})
    except TypeError as e:
        assert str(e) == "Tags must be hashable"
    else:
        assert False, "Expected a TypeError to be raised"

    try:
        job1.tag(1, "a", [])
    except TypeError as e:
        assert str(e) == "Tags must be hashable"
    else:
        assert False, "Expected a TypeError to be raised"

    job1.tag(0, "a", True)
    assert len(job1.tags) == 3