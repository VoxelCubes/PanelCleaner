"""
Batching of bubbles for translation requests.

Bubbles are grouped into fixed-size batches while preserving reading order, so the model
sees coherent runs of dialogue. Context windows expose the surrounding bubbles around a
batch as read-only reference text.

Pure functions, easy to unit-test.
"""

from attrs import frozen

BoxTuple = tuple[int, int, int, int]


@frozen
class Bubble:
    """A single source bubble to translate: its original index, geometry and text."""

    index: int
    box: BoxTuple
    text: str


def make_batches(bubbles: list[Bubble], batch_size: int) -> list[list[Bubble]]:
    """
    Split bubbles into batches of at most ``batch_size``, preserving order.

    :param bubbles: The bubbles to batch, already in reading order.
    :param batch_size: The maximum batch size (clamped to at least 1).
    :return: A list of batches.
    """
    size = max(1, batch_size)
    return [bubbles[i : i + size] for i in range(0, len(bubbles), size)]


def context_for_batch(
    all_bubbles: list[Bubble],
    batch: list[Bubble],
    window: int,
) -> tuple[list[str], list[str]]:
    """
    Compute the read-only context texts surrounding a batch.

    The context is taken from the full ordered bubble list (which may include bubbles
    that are skipped due to caching), so dialogue context stays intact even on re-runs.

    :param all_bubbles: All bubbles for the page, in reading order.
    :param batch: The batch being translated.
    :param window: How many bubbles of context to include on each side (0 disables it).
    :return: A tuple of (preceding texts, following texts).
    """
    if window <= 0 or not batch:
        return [], []

    index_by_identity = {id(b): i for i, b in enumerate(all_bubbles)}
    first = index_by_identity.get(id(batch[0]))
    last = index_by_identity.get(id(batch[-1]))
    if first is None or last is None:
        return [], []

    before = [b.text for b in all_bubbles[max(0, first - window) : first]]
    after = [b.text for b in all_bubbles[last + 1 : last + 1 + window]]
    return before, after
