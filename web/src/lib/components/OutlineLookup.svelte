<script lang="ts">
    import OutlineResults from "$lib/components/outline/OutlineResults.svelte";
    import {
        loadLookupBreakdown,
        type LookupBreakdown,
    } from "$lib/ploverApi";

    let outlineText = $state("");
    let searchedOutline = $state("");
    let lookupBreakdownData = $state<LookupBreakdown[]>([]);
    let lookupBreakdownError = $state<string | null>(null);
    let lookupBreakdownIsLoading = $state(false);

    const canLookup = $derived(
        !lookupBreakdownIsLoading
        && outlineText.trim() !== "",
    );

    const lookupOutline = async () => {
        const nextOutline = outlineText.trim();
        if (nextOutline === "") {
            return;
        }

        searchedOutline = nextOutline;
        lookupBreakdownIsLoading = true;
        lookupBreakdownError = null;

        try {
            lookupBreakdownData = await loadLookupBreakdown(nextOutline);
        } catch (error) {
            lookupBreakdownData = [];
            lookupBreakdownError = error instanceof Error ? error.message : String(error);
        } finally {
            lookupBreakdownIsLoading = false;
        }
    };
</script>

<section class="lookup-page" aria-labelledby="lookup-title">
    <header class="lookup-header">
        <div>
            <p class="eyebrow">Lookup by outline</p>
            <h1 id="lookup-title">Lookup by outline</h1>
        </div>

        <form
            class="lookup-form"
            onsubmit={(event) => {
                event.preventDefault();
                void lookupOutline();
            }}
        >
            <label>
                <span>Outline</span>
                <input
                    type="search"
                    bind:value={outlineText}
                    autocomplete="off"
                />
            </label>

            <button
                type="submit"
                class="button"
                disabled={!canLookup}
            >
                {lookupBreakdownIsLoading ? "Looking up" : "Lookup"}
            </button>
        </form>
    </header>

    <div class="lookup-shell">
        {#if lookupBreakdownIsLoading}
            <div class="message">Loading breakdown</div>
        {:else if lookupBreakdownError !== null}
            <div class="message is-error">Failed to load "{searchedOutline}": {lookupBreakdownError}</div>
        {:else if lookupBreakdownData.length > 0}
            <OutlineResults results={lookupBreakdownData} />
        {:else if searchedOutline.trim() !== ""}
            <div class="message">No lookup results for "{searchedOutline}"</div>
        {:else}
            <div class="message">Ready</div>
        {/if}
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

    .lookup-form label {
        display: grid;
        flex: 1 1 16rem;
        gap: 0.35rem;

        min-width: 0;
        color: oklch(0.28 0.028 160);
        font-size: 0.9rem;
        font-weight: 730;
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

    .button:disabled {
        cursor: wait;
        opacity: 0.65;
    }

    .lookup-shell {
        min-width: 0;
        min-height: 0;
        overflow: hidden;
        padding: 1rem;
        border: 0.0625rem solid oklch(0.84 0.016 155);
        border-radius: 0.5rem;
        background: oklch(0.995 0.002 160);
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

    @media (max-width: 48rem) {
        .lookup-header,
        .lookup-form {
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
    }
</style>
