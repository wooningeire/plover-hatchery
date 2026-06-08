<script lang="ts">
    import { base } from "$app/paths";
    import { page } from "$app/state";
    import type { Snippet } from "svelte";
    import "./index.scss";

    type NavItem = {
        href: string,
        label: string,
        matches: string[],
    };

    let {
        children,
    }: {
        children?: Snippet,
    } = $props();

    const navItems: NavItem[] = [
        {
            href: `${base}/dictionary`,
            label: "Dictionaries",
            matches: ["/", "/dictionary"],
        },
        {
            href: `${base}/translation`,
            label: "Lookup",
            matches: ["/translation"],
        },
        {
            href: `${base}/theory`,
            label: "Theory",
            matches: ["/theory"],
        },
    ];

    const appPath = $derived(
        page.url.pathname.startsWith(base)
            ? page.url.pathname.slice(base.length) || "/"
            : page.url.pathname,
    );

    const isActive = (item: NavItem) => (
        item.matches.some((match) => (
            appPath === match
            || (match !== "/" && appPath.startsWith(`${match}/`))
        ))
    );
</script>

<div class="app-shell">
    <aside class="app-sidebar" aria-label="Hatchery sections">
        <a class="brand" href={`${base}/`}>
            <span>Hatchery</span>
            <small>Plover tools</small>
        </a>

        <nav class="nav-tabs">
            {#each navItems as item}
                <a
                    href={item.href}
                    class:is-active={isActive(item)}
                >
                    {item.label}
                </a>
            {/each}
        </nav>
    </aside>

    <main class="app-content">
        {@render children?.()}
    </main>
</div>

<style lang="scss">
    .app-shell {
        display: grid;
        grid-template-columns: 14.5rem minmax(0, 1fr);

        width: 100vw;
        height: 100vh;
        min-width: 0;
        min-height: 0;
        overflow: hidden;
        background: oklch(0.96 0.011 150);
        color: oklch(0.2 0.028 160);
    }

    .app-sidebar {
        display: grid;
        align-content: start;
        gap: 1rem;

        min-width: 0;
        padding: 1rem;
        border-right: 0.0625rem solid oklch(0.84 0.018 155);
        background: oklch(0.985 0.004 155);
    }

    .brand {
        display: grid;
        gap: 0.15rem;

        min-height: 3.5rem;
        padding: 0.4rem 0.25rem;
        color: inherit;
        text-decoration: none;
    }

    .brand span {
        font-size: 1.15rem;
        font-weight: 800;
    }

    .brand small {
        color: oklch(0.46 0.03 170);
        font-size: 0.82rem;
        font-weight: 680;
    }

    .nav-tabs {
        display: grid;
        gap: 0.35rem;
    }

    .nav-tabs a {
        display: flex;
        align-items: center;

        min-width: 0;
        min-height: 2.5rem;
        padding: 0 0.75rem;
        border: 0.0625rem solid transparent;
        border-radius: 0.375rem;
        color: oklch(0.34 0.032 165);
        font-weight: 740;
        text-decoration: none;
    }

    .nav-tabs a:hover,
    .nav-tabs a.is-active {
        border-color: oklch(0.78 0.055 170);
        background: oklch(0.94 0.022 170);
        color: oklch(0.24 0.065 170);
    }

    .app-content {
        min-width: 0;
        min-height: 0;
        padding: 1rem;
        overflow: auto;
    }

    @media (max-width: 46rem) {
        .app-shell {
            grid-template-columns: 1fr;
            grid-template-rows: auto minmax(0, 1fr);
        }

        .app-sidebar {
            position: sticky;
            top: 0;
            z-index: 10;

            gap: 0.75rem;
            padding: 0.75rem;
            border-right: 0;
            border-bottom: 0.0625rem solid oklch(0.84 0.018 155);
        }

        .brand {
            min-height: 0;
            padding: 0;
        }

        .nav-tabs {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.4rem;
        }

        .nav-tabs a {
            justify-content: center;
            min-height: 2.25rem;
            padding-inline: 0.4rem;
            text-align: center;
        }

        .app-content {
            min-height: 0;
            padding: 0.75rem;
            overflow: auto;
        }
    }
</style>
