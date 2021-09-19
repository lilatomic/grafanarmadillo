def flat_map(f, xs):
    ys = []
    for x in xs:
        ys.extend(f(x))
    return ys
