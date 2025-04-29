# import itertools
# from plover_hatchery.lib.alignment.parse_morphology import Affix, Morpheme, Formatting, Root, split_morphology


# def _eq_chunks(chunks_1: "tuple[Root | Affix | Formatting, ...]", chunks_2: "tuple[Root | Affix | Formatting, ...]"):
#     for chunk_1, chunk_2 in itertools.zip_longest(chunks_1, chunks_2):
#         if chunk_1 is None or chunk_2 is None: return False

#         for part_1, part_2 in itertools.zip_longest(chunk_1.parts(), chunk_2.parts()):
#             if part_1 is None or part_2 is None: return False
#             if part_1.name != part_2.name: return False
#             if part_1.phono != part_2.phono: return False
#             if part_1.ortho != part_2.ortho: return False

#     return True


# def test__split_morphology__baseline():
#     morphology = split_morphology(" { * eir r }.> w ~ @@r r . dh == iy >.> E05 s t > ", "{air}>worth==y>>est>")

#     chunks = (
#         Root(),
#         Affix(True),
#         Affix(True),
#     )

#     chunks[0].morpheme_seq.append(Morpheme(chunks[0], "air", " * eir r ", ""))
#     chunks[1].morpheme_seq.append(Morpheme(chunks[1], "worth", " w ~ @@r r . dh ", ""))
#     chunks[1].morpheme_seq.append(Morpheme(chunks[1], "y", " iy ", ""))
#     chunks[2].morpheme_seq.append(Morpheme(chunks[2], "est", " E05 s t ", ""))


#     assert _eq_chunks(morphology.chunks, chunks)