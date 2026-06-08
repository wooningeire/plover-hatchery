<section class="theory-page" aria-labelledby="theory-title">
    <header>
        <p class="eyebrow">Theory</p>
        <h1 id="theory-title">Theory management</h1>
    </header>

    <div class="placeholder-panel">
        <h2>Placeholder</h2>
        <p>Theory management is not wired yet.</p>
    </div>
</section>

<style lang="scss">
    .theory-page {
        display: grid;
        gap: 1rem;

        min-width: 0;
    }

    header {
        display: grid;
        align-content: center;

        min-height: 4.5rem;
    }

    .eyebrow,
    h1,
    h2,
    p {
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

    h2 {
        color: oklch(0.24 0.028 160);
        font-size: 1.05rem;
        font-weight: 760;
    }

    p {
        color: oklch(0.38 0.03 165);
        line-height: 1.5;
    }

    .placeholder-panel {
        display: grid;
        gap: 0.5rem;

        min-height: 12rem;
        padding: 1rem;
        border: 0.0625rem solid oklch(0.84 0.016 155);
        border-radius: 0.5rem;
        background: oklch(0.995 0.002 160);
    }
</style>
