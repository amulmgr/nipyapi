#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nipyapi` _utils package."""

from __future__ import absolute_import
import pytest
from tests import conftest
import json
from ruamel.yaml import safe_load
from deepdiff import DeepDiff
from nipyapi import _utils, nifi
from nipyapi._utils import YAMLStreamError, RepresenterError
# Fix for Py3 introducing better IO errors, but not available in Py2
try:
    from nipyapi._utils import PermissionError, FileNotFoundError
except ImportError:
    pass


def test_json_default(fix_pg):
    f_pg = fix_pg.generate()
    r1 = _utils._json_default(f_pg.revision)
    assert isinstance(r1, dict)
    with pytest.raises(TypeError):
        _ = _utils._json_default({})


def test_dump(fix_flow_serde):
    # Testing that we don't modify or lose information in the round trip
    # Processing in memory for json
    export_obj = fix_flow_serde.snapshot
    ss_json = _utils.dump(
        obj=export_obj,
        mode='json'
    )
    assert isinstance(ss_json, str)
    round_trip_json = safe_load(ss_json)
    # assert that a basic match of the dicts is true
    assert round_trip_json == export_obj
    # Deepdiff returns an empty dict on no variations at a much deeper detail
    assert DeepDiff(
        export_obj,
        round_trip_json,
        verbose_level=2,
        ignore_order=False
    ) == {}
    with pytest.raises(ValueError):
        _ = _utils.dump('','FakeNews')
    with pytest.raises(TypeError):
        _ = _utils.dump({None}, 'json')
    # Test Yaml
    ss_yaml = _utils.dump(
        obj=export_obj,
        mode='yaml'
    )
    assert isinstance(ss_yaml, str)
    round_trip_yaml = safe_load(ss_yaml)
    assert round_trip_yaml == export_obj
    assert DeepDiff(
        export_obj,
        round_trip_yaml,
        verbose_level=2,
        ignore_order=False
    ) == {}
    assert round_trip_yaml == round_trip_json
    # Todo: test sorting


def test_load(fix_flow_serde):
    # Validating load testing again in case we break the 'dump' test
    r1 = _utils.load(
        obj=fix_flow_serde.json,
        dto=fix_flow_serde.dto
    )
    # Validate match
    assert DeepDiff(
        fix_flow_serde.snapshot.flow_contents,
        r1.flow_contents,
        verbose_level=2,
        ignore_order=True
    ) == {}
    with pytest.raises(YAMLStreamError):
        _ = _utils.load({})


def test_fs_write(tmpdir):
    f_fdir = tmpdir.mkdir(conftest.test_write_file_path)
    f_fpath = f_fdir.join(conftest.test_write_file_name)
    test_obj = conftest.test_write_file_name
    r1 = _utils.fs_write(
        obj=test_obj,
        file_path=f_fpath
    )
    assert r1 == test_obj
    # Test writing to an invalid location
    with pytest.raises(PermissionError):
        _ = _utils.fs_write(
            obj=test_obj,
            file_path='/dev/AlmostCertainlyNotAValidDevice'
        )
    # Test writing an invalid object
    with pytest.raises(TypeError):
        _ = _utils.fs_write(
            obj={},
            file_path=f_fpath
        )


def test_fs_read(fix_flow_serde, tmpdir):
    r1 = _utils.fs_read(
        file_path=fix_flow_serde.filepath + '.json'
    )
    assert r1 == fix_flow_serde.json
    # Test reading from unreachable file
    with pytest.raises(FileNotFoundError):
        _ = _utils.fs_read(
            file_path='/dev/AlmostCertainlyNotAValidDevice'
        )


def test_filter_obj(fix_pg):
    f_pg = fix_pg.generate()
    t_1 = ['pie']
    with pytest.raises(ValueError):
        _ = _utils.filter_obj(t_1, '', '')
    with pytest.raises(ValueError):
        _ = _utils.filter_obj([f_pg], '', 'pie')
    r1 = _utils.filter_obj([f_pg], 'nipyapi', 'name')
    assert isinstance(r1, nifi.ProcessGroupEntity)
    r2 = _utils.filter_obj([f_pg], 'FakeNews', 'name')
    assert r2 is None
    f_pg2 = fix_pg.generate()
    r3 = _utils.filter_obj([f_pg, f_pg2], 'nipyapi', 'name')
    assert isinstance(r3, list)
    r4 = _utils.filter_obj([], '', '')
    assert r4 is None