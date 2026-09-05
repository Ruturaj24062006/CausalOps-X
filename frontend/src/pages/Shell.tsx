export default function Shell() {
    return (
        <div className="card flex items-center justify-center flex-col gap-2" style={{ minHeight: 400, textAlign: 'center' }}>
            <div className="title text-muted" style={{ color: 'var(--brand-amber)', textTransform: 'uppercase' }}>
                {window.location.pathname.replace('/', '').replace('-', ' ')} UNAVAILABLE
            </div>
            <div className="subtitle text-small">This feature is not linked to the current live backend state.</div>
        </div>
    );
}
