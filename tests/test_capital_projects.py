import pytest

from skimodel.capital_projects.library import CapitalProjectLibrary, ProjectNotFoundError
from skimodel.capital_projects.models import CapitalProject, ProjectCategory


def test_add_and_list_project():
    library = CapitalProjectLibrary()
    project = library.add_project(CapitalProject(name="Test Lift", category=ProjectCategory.LIFT, total_cost=1_000_000))
    assert library.get_project(project.id) is project
    assert library.list_projects() == [project]


def test_remove_project():
    library = CapitalProjectLibrary()
    project = library.add_project(CapitalProject(name="Test Lift"))
    library.remove_project(project.id)
    with pytest.raises(ProjectNotFoundError):
        library.get_project(project.id)


def test_assign_timing_and_cost():
    library = CapitalProjectLibrary()
    project = library.add_project(CapitalProject(name="Lodge"))
    library.assign_timing(project.id, start_year_offset=2, duration_years=3)
    library.assign_cost(project.id, 5_000_000)
    updated = library.get_project(project.id)
    assert updated.start_year_offset == 2
    assert updated.duration_years == 3
    assert updated.total_cost == 5_000_000


def test_load_defaults(tmp_path):
    library = CapitalProjectLibrary()
    seed_file = tmp_path / "seed.json"
    seed_file.write_text(
        '[{"name": "Test Project", "category": "lift", "total_cost": 100}]', encoding="utf-8"
    )
    library.load_defaults(seed_file)
    assert len(library.list_projects()) == 1
    assert library.list_projects()[0].name == "Test Project"


def test_annual_spend_schedule_even_split():
    project = CapitalProject(name="X", total_cost=300, start_year_offset=1, duration_years=3)
    schedule = project.annual_spend_schedule()
    assert schedule == {1: 100.0, 2: 100.0, 3: 100.0}


def test_online_year_offset():
    project = CapitalProject(name="X", start_year_offset=1, duration_years=2)
    assert project.online_year_offset() == 3
