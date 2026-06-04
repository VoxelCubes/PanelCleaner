"""Tests for bubble batching and context windows."""

from pcleaner.translator.batching import Bubble, make_batches, context_for_batch


def make_bubbles(n):
    return [Bubble(index=i, box=(i, i, i + 1, i + 1), text=f"t{i}") for i in range(n)]


def test_make_batches_even():
    bubbles = make_bubbles(6)
    batches = make_batches(bubbles, 2)
    assert len(batches) == 3
    assert [b.index for b in batches[0]] == [0, 1]
    assert [b.index for b in batches[2]] == [4, 5]


def test_make_batches_remainder():
    batches = make_batches(make_bubbles(5), 2)
    assert [len(b) for b in batches] == [2, 2, 1]


def test_make_batches_clamps_size():
    batches = make_batches(make_bubbles(3), 0)
    assert len(batches) == 3  # size clamped to 1


def test_make_batches_empty():
    assert make_batches([], 4) == []


def test_context_for_batch_middle():
    bubbles = make_bubbles(6)
    batch = bubbles[2:4]  # indices 2,3
    before, after = context_for_batch(bubbles, batch, window=2)
    assert before == ["t0", "t1"]
    assert after == ["t4", "t5"]


def test_context_for_batch_at_edges():
    bubbles = make_bubbles(4)
    before, after = context_for_batch(bubbles, bubbles[0:2], window=2)
    assert before == []
    assert after == ["t2", "t3"]


def test_context_window_zero_disabled():
    bubbles = make_bubbles(4)
    assert context_for_batch(bubbles, bubbles[1:2], window=0) == ([], [])


def test_context_window_limits_size():
    bubbles = make_bubbles(10)
    batch = bubbles[5:6]
    before, after = context_for_batch(bubbles, batch, window=1)
    assert before == ["t4"]
    assert after == ["t6"]
