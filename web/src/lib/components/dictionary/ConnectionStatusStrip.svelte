<script lang="ts">
    import type { PloverConnectionState } from "./types";

    let {
        state,
        error,
    }: {
        state: PloverConnectionState,
        error: string | null,
    } = $props();
</script>

<section
    class="status-strip"
    class:is-success={state === "connected"}
    class:is-error={state === "error"}
    aria-live="polite"
>
    {#if state === "checking"}
        <span class="spinner"></span>
        <span>Checking Plover connection</span>
    {:else if state === "connected"}
        <span class="status-dot"></span>
        <span>Plover connection ready</span>
    {:else}
        <span class="status-dot"></span>
        <span>{error ?? "Could not connect to Plover"}</span>
    {/if}
</section>

<style lang="scss">
    @use "./dictionaryUi.scss" as ui;

    .status-strip {
        @include ui.message;

        justify-content: flex-start;
    }

    .status-strip.is-success {
        @include ui.success-message;
    }

    .status-strip.is-error {
        @include ui.error-message;
    }

    .status-dot,
    .spinner {
        width: 0.65rem;
        height: 0.65rem;
        flex: 0 0 auto;
        border-radius: 50%;
        background: currentColor;
    }

    .spinner {
        border: 0.125rem solid currentColor;
        border-right-color: transparent;
        background: transparent;
        animation: spin 0.72s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(1turn);
        }
    }
</style>
