# Copyright 2022 The jax3d Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for array_dataclass."""

from __future__ import annotations

import dataclasses

from etils import enp
from etils.array_types import IntArray, FloatArray  # pylint: disable=g-multiple-import
import jax.numpy as jnp
from jax3d import visu3d as v3d
from jax3d.visu3d.typing import Shape  # pylint: disable=g-multiple-import
import numpy as np
import pytest
import tensorflow.experimental.numpy as tnp


@pytest.fixture(scope='module', autouse=True)
def set_tnp():
  """Enable numpy behavior."""
  # This is required to have TF follow the same casting rules as numpy
  tnp.experimental_enable_numpy_behavior(prefer_float32=True)


@dataclasses.dataclass
class Point(v3d.DataclassArray):
  x: FloatArray[''] = v3d.array_field(shape=())
  y: FloatArray[''] = v3d.array_field(shape=())


@dataclasses.dataclass(frozen=True)
class Isometrie(v3d.DataclassArray):
  r: FloatArray['3 3'] = v3d.array_field(shape=(3, 3))
  t: IntArray['2'] = v3d.array_field(shape=(2,), dtype=int)


def _assert_point(p: Point, shape: Shape, xnp: enp.NpModule = None):
  """Validate the point."""
  xnp = xnp or np
  assert isinstance(p, Point)
  assert p.shape == shape
  assert p.x.shape == shape
  assert p.y.shape == shape
  assert p.x.dtype == np.float32
  assert p.y.dtype == np.float32
  assert p.xnp is xnp
  assert isinstance(p.x, xnp.ndarray)
  assert isinstance(p.y, xnp.ndarray)


def _assert_isometrie(p: Isometrie, shape: Shape, xnp: enp.NpModule = None):
  """Validate the point."""
  xnp = xnp or np
  assert isinstance(p, Isometrie)
  assert p.shape == shape
  assert p.r.shape == shape + (3, 3)
  assert p.t.shape == shape + (2,)
  assert p.r.dtype == np.float32
  assert p.t.dtype == np.int32
  assert p.xnp is xnp
  assert isinstance(p.r, xnp.ndarray)
  assert isinstance(p.t, xnp.ndarray)


@pytest.mark.parametrize('xnp', [None, np, jnp, tnp])
@pytest.mark.parametrize('x, y, shape', [
    (1, 2, ()),
    ([1, 2], [3, 4], (2,)),
    ([[1], [2]], [[3], [4]], (2, 1)),
])
def test_point_infered_np(
    xnp: enp.NpModule,
    x,
    y,
    shape: Shape,
):
  if xnp is not None:  # Normalize np arrays to test the various backend
    x = xnp.array(x)
    y = xnp.array(y)
  else:
    xnp = np

  p = Point(x=x, y=y)
  _assert_point(p, shape, xnp=xnp)


@pytest.mark.parametrize('xnp', [np, jnp, tnp])
def test_point(xnp: enp.NpModule):
  p = Point(
      x=xnp.zeros((3, 2)),
      y=xnp.zeros((3, 2)),
  )
  _assert_point(p, (3, 2), xnp=xnp)
  _assert_point(p.reshape((2, 1, 3, 1, 1)), (2, 1, 3, 1, 1), xnp=xnp)
  _assert_point(p.flatten(), (6,), xnp=xnp)

  p0, p1, p2 = list(p)
  _assert_point(p0, (2,), xnp=xnp)
  _assert_point(p1, (2,), xnp=xnp)
  _assert_point(p2, (2,), xnp=xnp)

  _assert_point(v3d.stack([p0, p0, p1, p1]), (4, 2), xnp=xnp)


@pytest.mark.parametrize('xnp', [np, jnp, tnp])
def test_isometrie(xnp: enp.NpModule):
  p = Isometrie(
      r=xnp.zeros((3, 2, 1, 1, 3, 3)),
      t=xnp.zeros((3, 2, 1, 1, 2)),
  )
  _assert_isometrie(p, (3, 2, 1, 1), xnp=xnp)
  _assert_isometrie(p.reshape((2, 1, 3, 1, 1)), (2, 1, 3, 1, 1), xnp=xnp)
  _assert_isometrie(p.flatten(), (6,), xnp=xnp)

  p0, p1, p2 = list(p)
  _assert_isometrie(p0, (2, 1, 1), xnp=xnp)
  _assert_isometrie(p1, (2, 1, 1), xnp=xnp)
  _assert_isometrie(p2, (2, 1, 1), xnp=xnp)

  _assert_isometrie(v3d.stack([p0, p0, p1, p1]), (4, 2, 1, 1), xnp=xnp)


def test_isometrie_wrong_input():
  # Incompatible types
  with pytest.raises(ValueError, match='Conflicting numpy types'):
    _ = Isometrie(
        r=enp.lazy.jnp.zeros((3, 3)),
        t=np.zeros((2,)),
    )

  # Bad inner shape
  with pytest.raises(ValueError, match='last dimensions to be'):
    _ = Isometrie(
        r=np.zeros((3, 2)),
        t=np.zeros((2,)),
    )

  # Bad batch shape
  with pytest.raises(ValueError, match='Conflicting batch shapes'):
    _ = Isometrie(
        r=np.zeros((2, 3, 3)),
        t=np.zeros((3, 2)),
    )

  # Bad reshape
  p = Isometrie(
      r=np.zeros((3, 3, 3)),
      t=np.zeros((3, 2)),
  )
  with pytest.raises(ValueError, match='cannot reshape array'):
    p.reshape((2, 2))
