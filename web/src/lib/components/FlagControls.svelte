<script lang="ts">
    export interface FlagSettings {
        opacity: number;
        strokeWidth: number;
        dashed: boolean;
        dashLength: number;
    }

    interface Props {
        flags: string[];
        settings: Record<string, FlagSettings>;
    }

    let { flags, settings = $bindable() }: Props = $props();
</script>

<div class="controls">
    <h3>Transition Flags</h3>

    <div class="controls-grid">
        {#if flags.length === 0}
            <div class="empty">No flags found</div>
        {/if}

        {#each flags as flag}
            <div class="flag-name">{flag}</div>

            <div class="control-row">
                <label class="opacity-control">
                    Opacity
                    <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step={Number.EPSILON} 
                        bind:value={settings[flag].opacity} 
                    />
                    <span class="value">{settings[flag].opacity.toFixed(2)}</span>
                </label>
                <label class="stroke-width-control">
                    Width
                    <input 
                        type="range" 
                        min="0.1" 
                        max="30" 
                        step={Number.EPSILON} 
                        bind:value={settings[flag].strokeWidth} 
                    />
                    <span class="value">{settings[flag].strokeWidth}</span>
                </label>
                <label class="dashed-control">
                    <input 
                        type="checkbox" 
                        bind:checked={settings[flag].dashed} 
                    />
                    Dashed
                </label>
                {#if settings[flag].dashed}
                    <label class="dash-length-control">
                        Dash
                        <input 
                            type="range" 
                            min="0.1" 
                            max="100" 
                            step={Number.EPSILON} 
                            bind:value={settings[flag].dashLength} 
                        />
                        <span class="value">{settings[flag].dashLength}</span>
                    </label>
                {/if}
            </div>
        {/each}
    </div>
</div>

<style>
.controls {
    padding: 1rem;
}

h3 {
    font-weight: 700;
}

.controls-grid {
    display: grid;
    grid-template-columns: repeat(2, auto);
    gap: 1rem;
}

.flag-name {
    display: block;
    margin-bottom: 0.5rem;
}
.control-row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;

    font-size: 0.8rem;
}
.opacity-control,
.stroke-width-control,
.dash-length-control {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.dashed-control {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    cursor: pointer;
}
</style>
