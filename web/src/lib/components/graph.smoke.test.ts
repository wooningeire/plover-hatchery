import {
    graphNodeX,
    graphViewBoxWidth,
    scaledNodeSpacing,
} from "./graph.js";

const assertEquals = (actual: unknown, expected: unknown) => {
    const actualJson = JSON.stringify(actual);
    const expectedJson = JSON.stringify(expected);

    if (actualJson !== expectedJson) {
        throw new Error(`Expected ${expectedJson}, got ${actualJson}`);
    }
};

const test = (name: string, callback: () => void) => {
    callback();
    console.log(`ok - ${name}`);
};

const nodeX = (index: number, spacingScale: number) => graphNodeX({
    index,
    paddingX: 50,
    nodeSpacing: 200,
    spacingScale,
});

test("graphNodeX left-aligns every node when spacing scale is zero", () => {
    assertEquals(
        [0, 1, 2, 7].map((index) => nodeX(index, 0)),
        [50, 50, 50, 50],
    );
});

test("graphNodeX preserves existing spacing when spacing scale is one", () => {
    assertEquals(
        [0, 1, 2, 7].map((index) => nodeX(index, 1)),
        [50, 250, 450, 1450],
    );
});

test("scaledNodeSpacing clamps spacing scale to the supported range", () => {
    assertEquals(scaledNodeSpacing(200, -1), 0);
    assertEquals(scaledNodeSpacing(200, 2), 200);
    assertEquals(scaledNodeSpacing(200, Number.NaN), 200);
});

test("graphViewBoxWidth uses the scaled spacing", () => {
    assertEquals(
        graphViewBoxWidth({
            nodeCount: 6,
            paddingX: 50,
            nodeSpacing: 200,
            spacingScale: 0.5,
            minWidth: 0,
        }),
        600,
    );
});
