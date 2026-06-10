import {
    expect,
    test,
} from "vitest";
import {
    graphNodeX,
    graphViewBoxWidth,
    scaledNodeSpacing,
} from "../src/lib/components/graph.js";


const nodeX = (index: number, spacingScale: number) => graphNodeX({
    index,
    paddingX: 50,
    nodeSpacing: 200,
    spacingScale,
});


test("graphNodeX left-aligns every node when spacing scale is zero", () => {
    expect(
        [0, 1, 2, 7].map((index) => nodeX(index, 0)),
    ).toEqual([50, 50, 50, 50]);
});

test("graphNodeX preserves existing spacing when spacing scale is one", () => {
    expect(
        [0, 1, 2, 7].map((index) => nodeX(index, 1)),
    ).toEqual([50, 250, 450, 1450]);
});

test("scaledNodeSpacing clamps spacing scale to the supported range", () => {
    expect(scaledNodeSpacing(200, -1)).toBe(0);
    expect(scaledNodeSpacing(200, 2)).toBe(200);
    expect(scaledNodeSpacing(200, Number.NaN)).toBe(200);
});

test("graphViewBoxWidth uses the scaled spacing", () => {
    expect(graphViewBoxWidth({
        nodeCount: 6,
        paddingX: 50,
        nodeSpacing: 200,
        spacingScale: 0.5,
        minWidth: 0,
    })).toBe(600);
});
