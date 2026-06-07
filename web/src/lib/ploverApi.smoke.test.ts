/**
 * n.b. this is not an automated test script; test with Plover's Hatchery web extension on and off
 */

import {
    PloverApiError,
    loadPloverDictionaries,
} from "./ploverApi.js";

type FetchImplementation = typeof fetch;


const originalFetch = globalThis.fetch;

function assert(condition: unknown, message: string): asserts condition {
    if (!condition) {
        throw new Error(message);
    }
}

const withFetch = async (
    fetchImplementation: FetchImplementation,
    callback: () => Promise<void>,
) => {
    globalThis.fetch = fetchImplementation;

    try {
        await callback();
    } finally {
        globalThis.fetch = originalFetch;
    }
};

const jsonResponse = (value: unknown, init?: ResponseInit) => (
    new Response(JSON.stringify(value), {
        status: 200,
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...init?.headers,
        },
    })
);

const assertRejectsWithPloverApiError = async (
    callback: () => Promise<unknown>,
    expectedKind: PloverApiError["kind"],
    expectedMessageText: string,
) => {
    try {
        await callback();
    } catch (error) {
        assert(error instanceof PloverApiError, "Expected a PloverApiError");
        assert(error.kind === expectedKind, `Expected ${expectedKind}, got ${error.kind}`);
        assert(
            error.message.includes(expectedMessageText),
            `Expected message to include "${expectedMessageText}", got "${error.message}"`,
        );
        return;
    }

    throw new Error("Expected promise to reject");
};

const test = async (name: string, callback: () => Promise<void>) => {
    await callback();
    console.log(`ok - ${name}`);
};


await test("loadPloverDictionaries reports when local Plover is unreachable", async () => {
    await withFetch(
        () => Promise.reject(new TypeError("fetch failed")),
        async () => {
            await assertRejectsWithPloverApiError(
                () => loadPloverDictionaries(),
                "connection",
                "Could not reach the Hatchery API",
            );
        },
    );
});

await test("loadPloverDictionaries reports when another service uses the Plover port", async () => {
    await withFetch(
        () => Promise.resolve(jsonResponse({
            ok: true,
        })),
        async () => {
            await assertRejectsWithPloverApiError(
                () => loadPloverDictionaries(),
                "wrong-server",
                "it is not the Hatchery API",
            );
        },
    );
});

await test("loadPloverDictionaries accepts Hatchery status before reading dictionaries", async () => {
    const requestedPaths: string[] = [];

    await withFetch(
        (input) => {
            const url = String(input);
            requestedPaths.push(new URL(url).pathname);

            if (url.endsWith("/api/status")) {
                return Promise.resolve(jsonResponse({
                    service: "plover-hatchery",
                    ok: true,
                }));
            }

            return Promise.resolve(jsonResponse({
                dictionaries: [
                    {
                        path: "user.hatchery",
                        label: "user.hatchery",
                    },
                ],
            }));
        },
        async () => {
            const response = await loadPloverDictionaries();

            assert(requestedPaths.join(",") === "/api/status,/api/dictionaries", "Expected status check before dictionaries request");
            assert(response.dictionaries.length === 1, "Expected one dictionary");
            assert(response.dictionaries[0]?.path === "user.hatchery", "Expected dictionary path");
        },
    );
});
