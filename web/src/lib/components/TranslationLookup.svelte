<script lang="ts">
    import { onMount } from "svelte";
    import Graph from "$lib/components/Graph.svelte";
    import {
        loadLookupBreakdown,
        loadTranslationBreakdown,
        type TranslationBreakdown,
    } from "$lib/ploverApi";

    let {
        initialTranslation = "",
        autoLookup = false,
    }: {
        initialTranslation?: string,
        autoLookup?: boolean,
    } = $props();

    const getInitialTranslation = () => initialTranslation;

    let translationText = $state(getInitialTranslation());
    let searchedTranslation = $state(getInitialTranslation());
    let translationBreakdownData = $state<TranslationBreakdown[]>([]);
    let translationBreakdownError = $state<string | null>(null);
    let translationBreakdownIsLoading = $state(false);
    let breakdownIndex = $state(0);

    let testOutline = $state("");
    let lookupBreakdownData = $state<any[] | null>(null);
    let lookupBreakdownError = $state<string | null>(null);
    let lookupRequestId = 0;
    let lookupTimeoutId: ReturnType<typeof setTimeout> | null = null;

    const breakdown = $derived(translationBreakdownData[breakdownIndex] ?? null);
    const breakdownCount = $derived(translationBreakdownData.length);
    const canLookup = $derived(
        !translationBreakdownIsLoading
        && translationText.trim() !== "",
    );

    onMount(() => {
        if (autoLookup && translationText.trim() !== "") {
            void lookupTranslation();
        }
    });

    $effect(() => {
        const nextTestOutline = testOutline.trim();

        if (nextTestOutline === "" || breakdown === null) {
            lookupRequestId += 1;
            lookupBreakdownData = null;
            lookupBreakdownError = null;
            return;
        }

        if (lookupTimeoutId !== null) {
            clearTimeout(lookupTimeoutId);
        }

        const requestId = lookupRequestId + 1;
        lookupRequestId = requestId;
        lookupBreakdownData = null;
        lookupBreakdownError = null;

        lookupTimeoutId = setTimeout(async () => {
            try {
                const nextLookupBreakdownData = await loadLookupBreakdown(nextTestOutline);
                if (requestId !== lookupRequestId) {
                    return;
                }

                lookupBreakdownData = nextLookupBreakdownData;
                lookupBreakdownError = null;
            } catch (error) {
                if (requestId !== lookupRequestId) {
                    return;
                }

                lookupBreakdownData = null;
                lookupBreakdownError = error instanceof Error ? error.message : String(error);
            }
        }, 80);

        return () => {
            if (lookupTimeoutId !== null) {
                clearTimeout(lookupTimeoutId);
            }
        };
    });

    const lookupTranslation = async () => {
        const nextTranslation = translationText.trim();
        if (nextTranslation === "") {
            return;
        }

        searchedTranslation = nextTranslation;
        translationBreakdownIsLoading = true;
        translationBreakdownError = null;
        lookupRequestId += 1;
        lookupBreakdownData = null;
        lookupBreakdownError = null;

        try {
            translationBreakdownData = await loadTranslationBreakdown(nextTranslation);
            breakdownIndex = 0;
        } catch (error) {
            translationBreakdownData = [];
            translationBreakdownError = error instanceof Error ? error.message : String(error);
        } finally {
            translationBreakdownIsLoading = false;
        }
    };

    const previousBreakdown = () => {
        if (breakdownCount === 0) {
            return;
        }

        breakdownIndex = breakdownIndex === 0 ? breakdownCount - 1 : breakdownIndex - 1;
    };

    const nextBreakdown = () => {
        if (breakdownCount === 0) {
            return;
        }

        breakdownIndex = breakdownIndex === breakdownCount - 1 ? 0 : breakdownIndex + 1;
    };
</script>

<section class="lookup-page" aria-labelledby="lookup-title">
    <header class="lookup-header">
        <div>
            <p class="eyebrow">Lookup</p>
            <h1 id="lookup-title">Translation lookup</h1>
        </div>

        <form
            class="lookup-form"
            onsubmit={(event) => {
                event.preventDefault();
                void lookupTranslation();
            }}
        >
            <label>
                <span>Translation</span>
                <input
                    type="search"
                    bind:value={translationText}
                    autocomplete="off"
                />
            </label>

            <button
                type="submit"
                class="button"
                disabled={!canLookup}
            >
                {translationBreakdownIsLoading ? "Looking up" : "Lookup"}
            </button>
        </form>
    </header>

    <div
        class="lookup-shell"
        class:has-breakdown={breakdown !== null}
    >
        <section class="entry-controls" aria-label="Breakdown entries">
            <button
                type="button"
                class="button secondary compact"
                disabled={breakdownCount === 0}
                onclick={previousBreakdown}
            >
                Previous
            </button>

            <button
                type="button"
                class="button secondary compact"
                disabled={breakdownCount === 0}
                onclick={nextBreakdown}
            >
                Next
            </button>

            <div class="entry-number">
                Entry {breakdownCount === 0 ? 0 : breakdownIndex + 1} / {breakdownCount}
            </div>

            <code title={breakdown?.entry ?? ""}>{breakdown?.entry ?? ""}</code>
        </section>

        {#if translationBreakdownIsLoading}
            <div class="message">Loading breakdown</div>
        {:else if translationBreakdownError !== null}
            <div class="message is-error">Failed to load "{searchedTranslation}": {translationBreakdownError}</div>
        {:else if breakdown !== null}
            <div class="graph-frame">
                <Graph
                    data={breakdown.subtrie}
                    highlightData={lookupBreakdownData}
                />
            </div>
        {:else if searchedTranslation.trim() !== ""}
            <div class="message">No breakdown found for "{searchedTranslation}"</div>
        {:else}
            <div class="message">Ready</div>
        {/if}

        <div class="outline-panel">
            <label class="test-outline">
                <span>Test outline</span>
                <input
                    type="text"
                    bind:value={testOutline}
                    autocomplete="off"
                />
            </label>

            {#if lookupBreakdownError !== null}
                <div class="message is-error compact" aria-live="polite">
                    Outline highlight failed: {lookupBreakdownError}
                </div>
            {/if}
        </div>
    </div>
</section>

<style lang="scss">
    .lookup-page {
        display: grid;
        grid-template-rows: auto minmax(0, 1fr);
        gap: 1rem;

        width: 100%;
        height: 100%;
        min-width: 0;
        min-height: 0;
    }

    .lookup-header,
    .lookup-form,
    .entry-controls,
    .test-outline,
    .message {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .lookup-header {
        justify-content: space-between;
        min-height: 4.5rem;
    }

    .eyebrow,
    h1 {
        margin: 0;
    }

    .eyebrow {
        color: oklch(0.42 0.035 170);
        font-size: 0.76rem;
        font-weight: 760;
        letter-spacing: 0;
        text-transform: uppercase;
    }

    h1 {
        color: oklch(0.2 0.028 160);
        font-size: 1.55rem;
        font-weight: 780;
    }

    .lookup-form {
        width: min(34rem, 100%);
        justify-content: flex-end;
    }

    .lookup-form label,
    .test-outline {
        display: grid;
        gap: 0.35rem;

        min-width: 0;
        color: oklch(0.28 0.028 160);
        font-size: 0.9rem;
        font-weight: 730;
    }

    .lookup-form label {
        flex: 1 1 16rem;
    }

    .lookup-shell {
        display: grid;
        grid-template-rows: auto auto auto;
        align-content: start;
        gap: 0.75rem;

        min-width: 0;
        min-height: 0;
        overflow: hidden;
        padding: 1rem;
        border: 0.0625rem solid oklch(0.84 0.016 155);
        border-radius: 0.5rem;
        background: oklch(0.995 0.002 160);
    }

    .lookup-shell.has-breakdown {
        grid-template-rows: auto minmax(0, 1fr) auto;
        align-content: stretch;
    }

    .entry-controls {
        min-width: 0;
        min-height: 3rem;
        padding-bottom: 0.75rem;
        border-bottom: 0.0625rem solid oklch(0.88 0.012 160);
    }

    .entry-controls code {
        min-width: 0;
        overflow: hidden;
        color: oklch(0.24 0.028 160);
        font-family: "Atkinson Hyperlegible Mono", monospace;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .entry-number {
        flex: 0 0 auto;
        color: oklch(0.38 0.03 165);
        font-size: 0.88rem;
        font-weight: 760;
    }

    .graph-frame {
        min-width: 0;
        min-height: 0;
        overflow: hidden;
        border: 0.0625rem solid oklch(0.88 0.012 160);
        border-radius: 0.375rem;
    }

    .graph-frame :global(.graph-container) {
        width: 100%;
        height: 100%;
        min-height: 0;
    }

    .outline-panel {
        display: grid;
        gap: 0.5rem;

        min-width: 0;
    }

    .message {
        min-height: 2.5rem;
        align-self: start;
        padding: 0.6rem 0.75rem;
        border: 0.0625rem solid oklch(0.84 0.018 155);
        border-radius: 0.375rem;
        background: oklch(0.97 0.008 155);
        color: oklch(0.36 0.025 160);
        font-size: 0.92rem;
    }

    .message.is-error {
        border-color: oklch(0.82 0.08 28);
        background: oklch(0.97 0.035 28);
        color: oklch(0.42 0.13 28);
    }

    .message.compact {
        min-height: 2rem;
        padding: 0.45rem 0.65rem;
        font-size: 0.84rem;
    }

    .test-outline {
        grid-template-columns: auto minmax(0, 1fr);
        align-items: center;
    }

    input {
        width: 100%;
        min-width: 0;
        height: 2.4rem;
        padding: 0 0.7rem;
        border: 0.0625rem solid oklch(0.76 0.018 160);
        border-radius: 0.375rem;
        background: oklch(1 0 0);
        color: oklch(0.2 0.028 160);
    }

    input:focus {
        border-color: oklch(0.5 0.12 160);
        outline: 0.125rem solid oklch(0.86 0.075 160);
        outline-offset: 0.0625rem;
    }

    .button {
        min-width: 6.5rem;
        min-height: 2.4rem;
        padding: 0 0.9rem;
        border: 0.0625rem solid oklch(0.48 0.11 160);
        border-radius: 0.375rem;
        background: oklch(0.5 0.12 160);
        color: oklch(0.99 0.002 160);
        cursor: pointer;
        font-weight: 760;
    }

    .button:hover:not(:disabled) {
        background: oklch(0.44 0.12 160);
    }

    .button.secondary {
        border-color: oklch(0.78 0.018 160);
        background: oklch(0.99 0.002 160);
        color: oklch(0.28 0.028 160);
    }

    .button.secondary:hover:not(:disabled) {
        background: oklch(0.95 0.012 160);
    }

    .button.compact {
        min-width: 5.5rem;
        min-height: 2rem;
        padding-inline: 0.6rem;
        font-size: 0.84rem;
    }

    .button:disabled {
        cursor: wait;
        opacity: 0.65;
    }

    @media (max-width: 48rem) {
        .lookup-header,
        .lookup-form,
        .entry-controls,
        .test-outline {
            align-items: stretch;
            flex-direction: column;
        }

        .lookup-form,
        .lookup-form .button {
            width: 100%;
        }

        .lookup-form label {
            flex: none;
        }

        .entry-controls code {
            white-space: normal;
        }
    }
</style>
