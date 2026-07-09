from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class InitResult:
    created_dirs: int = 0
    created_files: int = 0
    skipped_files: int = 0
    planned_actions: int = 0


@dataclass
class NewChapterResult:
    created_dirs: int = 0
    created_files: int = 0
    skipped_files: int = 0
    planned_actions: int = 0
    paths: list[str] = field(default_factory=list)


@dataclass
class NewBookResult:
    created_dirs: int = 0
    created_files: int = 0
    skipped_files: int = 0
    planned_actions: int = 0
    paths: list[str] = field(default_factory=list)


@dataclass
class AdoptFile:
    path: str
    layer: str
    role: str
    migration_phase: str
    suggested_target_path: str
    extension: str
    bytes: int
    nonspace_chars: int


@dataclass
class AdoptLayerSummary:
    layer: str
    files: int
    nonspace_chars: int


@dataclass
class AdoptRisk:
    severity: str
    code: str
    message: str


@dataclass
class AdoptCopy:
    source_path: str
    target_path: str
    status: str
    message: str


@dataclass
class AdoptReport:
    target: str
    output_file: str | None
    dry_run: bool
    written: bool
    scanned_files: int
    included_files: int
    ignored_files: int
    total_nonspace_chars: int
    layer_summaries: list[AdoptLayerSummary]
    files: list[AdoptFile]
    risks: list[AdoptRisk]
    next_actions: list[str]
    copy_to: str | None = None
    copied_files: int = 0
    skipped_files: int = 0
    planned_copies: int = 0
    copy_files: list[AdoptCopy] = field(default_factory=list)


@dataclass
class AdoptReviewCheck:
    name: str
    source_command: str
    status: str
    issue_count: int
    blocking_issue_count: int
    summary: str


@dataclass
class AdoptReviewIssue:
    severity: str
    source: str
    code: str
    subject: str
    path: str
    message: str


@dataclass
class AdoptReviewWaiver:
    source: str
    code: str
    subject: str
    path: str
    reason: str
    owner: str = ""
    until: str = ""


@dataclass
class AdoptReviewReport:
    target: str
    book: str
    output_file: str | None
    dry_run: bool
    written: bool
    status: str
    ready: bool
    standard_project: bool
    migration_files: int
    import_queue_files: int
    total_issue_count: int
    issue_count: int
    blocking_issue_count: int
    waived_issue_count: int
    waiver_file: str | None
    waivers: list[AdoptReviewWaiver]
    max_issues: int
    omitted_issues: int
    checks: list[AdoptReviewCheck]
    issues: list[AdoptReviewIssue]
    next_actions: list[str]
    doctor: object
    info: object
    characters: object
    book_gate: object | None


@dataclass
class AdoptTaskGroup:
    phase: str
    priority: str
    code: str
    count: int
    blocking_count: int
    areas: list[str]
    source_commands: list[str]
    sample_subjects: list[str]
    sample_paths: list[str]
    suggested_action: str


@dataclass
class AdoptPlanReport:
    target: str
    book: str
    output_file: str | None
    dry_run: bool
    written: bool
    review_status: str
    review_ready: bool
    task_count: int
    priority_counts: dict[str, int]
    task_groups: list[AdoptTaskGroup]
    group_output_dir: str | None
    group_files_written: int
    group_files: list[str]
    tasks: list[RevisionTask]
    next_actions: list[str]
    adopt_review: AdoptReviewReport


@dataclass
class ImportPlanItem:
    source_path: str
    inferred_book: str
    inferred_chapter: str
    title: str
    target_path: str
    status: str
    scaffold_status: str
    confidence: str
    reason: str
    nonspace_chars: int


@dataclass
class ImportPlanReport:
    target: str
    book: str
    output_file: str | None
    dry_run: bool
    apply: bool
    create_scaffolds: bool
    replace_placeholder_targets: bool
    written: bool
    import_queue_files: int
    displayed_items: int
    omitted_items: int
    ready_count: int
    moved_files: int
    replaced_placeholder_targets: int
    scaffold_created_files: int
    scaffold_skipped_files: int
    scaffold_planned_actions: int
    needs_review_count: int
    target_exists_count: int
    placeholder_target_count: int
    duplicate_target_count: int
    items: list[ImportPlanItem]
    next_actions: list[str]


@dataclass
class ExportCleanChapter:
    chapter: str
    source_file: str
    chars: int
    nonspace_chars: int
    cjk_chars: int
    lines: int


@dataclass
class ExportCleanResult:
    target: str
    book: str
    output_file: str
    title: str
    chapter_count: int
    total_chars: int
    total_nonspace_chars: int
    total_cjk_chars: int
    dry_run: bool
    chapters: list[ExportCleanChapter]


@dataclass
class PublishAuditChapter:
    chapter: str
    heading: str
    line: int
    chars: int
    nonspace_chars: int
    cjk_chars: int
    lines: int


@dataclass
class PublishAuditIssue:
    severity: str
    code: str
    chapter: str
    line: int | None
    message: str


@dataclass
class PublishAuditReport:
    target: str
    book: str
    clean_file: str
    clean_file_exists: bool
    draft_chapters: int
    clean_chapters: int
    total_nonspace_chars: int
    total_cjk_chars: int
    issues: list[PublishAuditIssue]
    chapters: list[PublishAuditChapter]


@dataclass
class PublishMetadataIssue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class PublishMetadataReport:
    target: str
    book: str
    checklist_file: str
    checklist_file_exists: bool
    output_file: str | None
    dry_run: bool
    written: bool
    metadata: dict[str, object]
    issues: list[PublishMetadataIssue]


@dataclass
class PublishCopyIssue:
    severity: str
    code: str
    source: str
    path: str
    message: str


@dataclass
class PublishCopySource:
    name: str
    path: str
    exists: bool
    nonspace_chars: int
    preview: str


@dataclass
class PublishCopyReport:
    target: str
    book: str
    output_file: str | None
    dry_run: bool
    written: bool
    checklist_file: str
    clean_file: str
    outline_file: str
    seed_file: str
    metadata: dict[str, object]
    suggested_metadata: dict[str, object]
    title_candidates: list[str]
    tag_candidates: list[str]
    keyword_candidates: list[str]
    chapter_titles: list[str]
    sources: list[PublishCopySource]
    issues: list[PublishCopyIssue]


@dataclass
class PublishManifestFile:
    kind: str
    path: str
    exists: bool
    bytes: int
    sha256: str
    chars: int
    nonspace_chars: int
    cjk_chars: int
    lines: int


@dataclass
class PublishManifestIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class PublishManifestReport:
    target: str
    book: str
    output_file: str
    dry_run: bool
    written: bool
    clean_file: str
    metadata_file: str
    manifest: dict[str, object]
    files: list[PublishManifestFile]
    issues: list[PublishManifestIssue]


@dataclass
class PublishEpubChapter:
    chapter: str
    title: str
    file: str
    nonspace_chars: int


@dataclass
class PublishEpubIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class PublishEpubReport:
    target: str
    book: str
    output_file: str
    manifest_file: str
    manifest_file_exists: bool
    clean_file: str
    metadata_file: str
    cover_file: str
    cover_file_exists: bool
    dry_run: bool
    written: bool
    chapter_count: int
    total_nonspace_chars: int
    metadata: dict[str, object]
    chapters: list[PublishEpubChapter]
    issues: list[PublishEpubIssue]


@dataclass
class EpubAuditIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class EpubAuditReport:
    target: str
    book: str
    epub_file: str
    manifest_file: str
    clean_file: str
    metadata_file: str
    cover_file: str
    epub_file_exists: bool
    epub_valid: bool
    stale: bool
    mimetype_first: bool
    mimetype_valid: bool
    has_container: bool
    has_opf: bool
    has_nav: bool
    has_css: bool
    chapter_count: int
    has_cover_page: bool
    has_cover_image: bool
    opf_cover_declared: bool
    issues: list[EpubAuditIssue]


@dataclass
class ChapterPlan:
    source: str
    row: int
    chapter: str
    title: str = ""
    viewpoint: str = ""
    kind: str = ""
    pressure: str = ""
    desire: str = ""
    obstacle: str = ""
    change: str = ""
    remainder: str = ""
    target_chars: str = ""


@dataclass
class PlanChapterResult:
    outline_file: str
    engine_file: str
    plan_row: int
    updated_fields: list[str] = field(default_factory=list)
    skipped_fields: list[str] = field(default_factory=list)
    dry_run: bool = False


@dataclass
class PlanAuditChapter:
    chapter: str
    title: str
    row: int
    chapter_file: str | None
    engine_file: str | None
    engine_synced: bool
    missing_engine_fields: list[str] = field(default_factory=list)


@dataclass
class PlanAuditIssue:
    severity: str
    code: str
    chapter: str
    path: str
    message: str


@dataclass
class PlanAuditReport:
    target: str
    book: str
    outline_file: str
    planned_chapters: int
    chapter_files: int
    engine_files: int
    synced_engines: int
    chapters: list[PlanAuditChapter]
    issues: list[PlanAuditIssue]


@dataclass
class RetrospectiveChapter:
    chapter: str
    chapter_file: str
    retrospective_file: str | None
    retrospective_placeholder: bool
    actual_chars: str
    sync_items: list[str] = field(default_factory=list)


@dataclass
class RetrospectiveIssue:
    severity: str
    code: str
    chapter: str
    path: str
    message: str


@dataclass
class RetrospectiveReport:
    target: str
    book: str
    book_retrospective_file: str
    book_retrospective_exists: bool
    book_retrospective_placeholder: bool
    chapter_count: int
    retrospective_count: int
    missing_retrospectives: int
    placeholder_retrospectives: int
    sync_item_count: int
    chapters: list[RetrospectiveChapter]
    issues: list[RetrospectiveIssue]


@dataclass
class FileStats:
    path: str
    chars: int
    nonspace_chars: int
    cjk_chars: int
    latin_words: int
    lines: int
    band: str


@dataclass
class StatsReport:
    target: str
    mode: str
    metric: str
    file_count: int
    total: int
    average: int
    minimum: int
    maximum: int
    files: list[FileStats]


@dataclass
class ChapterWaveItem:
    index: int
    chapter: str
    path: str
    chars: int
    nonspace_chars: int
    cjk_chars: int
    lines: int
    metric_value: int
    band: str
    delta_from_previous: int | None


@dataclass
class ChapterWaveIssue:
    severity: str
    code: str
    chapter: str
    message: str


@dataclass
class ChapterWaveReport:
    target: str
    mode: str
    metric: str
    file_count: int
    total: int
    average: int
    minimum: int
    maximum: int
    spread: int
    spread_ratio_percent: int
    average_delta: int
    longest_flat_run: int
    longest_same_band_run: int
    band_counts: dict[str, int]
    issues: list[ChapterWaveIssue]
    chapters: list[ChapterWaveItem]


@dataclass
class CountItem:
    item: str
    count: int


@dataclass
class StyleAuditFile:
    path: str
    opening_type: str
    opening_preview: str
    ending_type: str
    ending_preview: str
    watch_total: int
    top_terms: list[CountItem]
    repeated_openings: list[CountItem]


@dataclass
class StyleAuditReport:
    target: str
    mode: str
    file_count: int
    watch_terms: list[str]
    watch_total: int
    opening_types: dict[str, int]
    ending_types: dict[str, int]
    aggregate_terms: list[CountItem]
    repeated_openings: list[CountItem]
    files: list[StyleAuditFile]


@dataclass
class WordScanFile:
    path: str
    chars: int
    nonspace_chars: int
    latin_words: int
    phrase_total: int
    top_terms: list[CountItem]
    watch_hits: list[CountItem]


@dataclass
class WordScanReport:
    target: str
    mode: str
    file_count: int
    min_count: int
    top: int
    watch_terms: list[str]
    total_latin_words: int
    total_phrases: int
    aggregate_terms: list[CountItem]
    watch_hits: list[CountItem]
    files: list[WordScanFile]


@dataclass
class TableCheckIssue:
    severity: str
    code: str
    path: str
    line: int
    message: str


@dataclass
class TableCheckTable:
    path: str
    line: int
    columns: int
    rows: int
    filled_cells: int
    empty_cells: int
    headers: list[str]
    issues: list[TableCheckIssue]


@dataclass
class TableCheckReport:
    target: str
    mode: str
    file_count: int
    table_count: int
    issue_count: int
    min_filled_cells: int
    issues: list[TableCheckIssue]
    tables: list[TableCheckTable]


@dataclass
class FileCheck:
    path: str
    kind: str
    exists: bool
    placeholder: bool


@dataclass
class ChapterContinuity:
    key: str
    chapter_file: str
    placeholder: bool
    engine_file: str | None
    engine_placeholder: bool
    retrospective_file: str | None
    retrospective_placeholder: bool


@dataclass
class ContinuityIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class ContinuityReport:
    target: str
    file_count: int
    chapter_count: int
    placeholder_chapters: int
    missing_engine_count: int
    missing_retrospective_count: int
    missing_standard_files: int
    placeholder_standard_files: int
    standard_files: list[FileCheck]
    chapters: list[ChapterContinuity]
    issues: list[ContinuityIssue]


@dataclass
class EchoThread:
    source: str
    row: int
    thread: str
    first_plant: str
    last_echo: str
    current_state: str
    next_light_echo: str
    do_not_reveal: str
    payoff_direction: str
    text_hits: int
    last_text_hit: str | None


@dataclass
class EchoIssue:
    severity: str
    code: str
    thread: str
    path: str
    message: str


@dataclass
class EchoReport:
    target: str
    table_files: list[str]
    chapter_count: int
    thread_count: int
    text_scan: bool
    issues: list[EchoIssue]
    threads: list[EchoThread]


@dataclass
class InfoBoundaryItem:
    source: str
    row: int
    item: str
    author_truth: str
    reader_state: str
    character_a: str
    character_b: str
    public_version: str
    official_version: str
    next_release: str
    forbidden: str
    text_hits: int
    first_text_hit: str | None
    last_text_hit: str | None


@dataclass
class InfoBoundaryIssue:
    severity: str
    code: str
    item: str
    path: str
    message: str


@dataclass
class InfoBoundaryReport:
    target: str
    table_files: list[str]
    chapter_count: int
    item_count: int
    text_scan: bool
    issues: list[InfoBoundaryIssue]
    items: list[InfoBoundaryItem]


@dataclass
class CharacterProfile:
    character: str
    arc_file: str | None
    index_row: int | None
    has_intelligence: bool
    has_voice: bool
    has_relationships: bool
    has_growth: bool
    has_failure_path: bool


@dataclass
class CharacterArcFile:
    path: str
    character: str
    placeholder: bool
    has_identity: bool
    has_start: bool
    has_intelligence: bool
    has_voice: bool
    has_relationships: bool
    has_growth: bool
    has_failure_path: bool


@dataclass
class CharacterAuditIssue:
    severity: str
    code: str
    character: str
    path: str
    message: str


@dataclass
class CharacterAuditReport:
    target: str
    index_file: str | None
    intelligence_file: str | None
    voice_file: str | None
    relationship_file: str | None
    arc_files: list[str]
    character_count: int
    arc_count: int
    index_count: int
    intelligence_count: int
    voice_count: int
    relationship_count: int
    issues: list[CharacterAuditIssue]
    characters: list[CharacterProfile]
    arcs: list[CharacterArcFile]


@dataclass
class ContextPackFile:
    role: str
    path: str
    required: bool
    exists: bool
    chars: int
    nonspace_chars: int
    included_chars: int
    truncated: bool
    content: str


@dataclass
class ContextPackIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class ContextPackReport:
    target: str
    task: str
    book: str
    chapter: str | None
    output_file: str | None
    dry_run: bool
    written: bool
    include_content: bool
    max_chars_per_file: int
    max_total_chars: int
    included_total_chars: int
    files: list[ContextPackFile]
    issues: list[ContextPackIssue]
    checklist: list[str]


@dataclass
class WorkflowPlanStep:
    stage: str
    order: int
    title: str
    purpose: str
    command: str
    required: bool
    produces: list[str]
    exit_checks: list[str]


@dataclass
class WorkflowPlanReport:
    target: str
    stage: str
    book: str
    chapter: str | None
    output_file: str | None
    dry_run: bool
    written: bool
    step_count: int
    commands: list[str]
    steps: list[WorkflowPlanStep]
    notes: list[str]


@dataclass
class ScenePlanScene:
    order: int
    title: str
    function: str
    focus: str
    pressure: str
    desire: str
    obstacle: str
    change: str
    remainder: str
    info_boundary: list[str]
    foreshadowing: list[str]
    exit_check: str


@dataclass
class ScenePlanIssue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class ScenePlanReport:
    target: str
    book: str
    chapter: str
    engine_file: str
    output_file: str | None
    dry_run: bool
    written: bool
    title: str
    viewpoint: str
    kind: str
    target_chars: str
    pressure: str
    desire: str
    obstacle: str
    change: str
    remainder: str
    scene_count: int
    scenes: list[ScenePlanScene]
    continuity: dict[str, str]
    information_boundaries: list[dict[str, str]]
    foreshadowing_threads: list[dict[str, str]]
    blank_requirements: dict[str, str]
    style_reminders: dict[str, str]
    issues: list[ScenePlanIssue]


@dataclass
class DraftBriefSceneTask:
    order: int
    title: str
    function: str
    writing_goal: str
    pressure: str
    desire: str
    obstacle: str
    guardrails: list[str]
    exit_check: str


@dataclass
class DraftBriefIssue:
    severity: str
    source: str
    code: str
    field: str
    message: str


@dataclass
class DraftBriefReport:
    target: str
    book: str
    chapter: str
    output_file: str | None
    dry_run: bool
    written: bool
    include_context_content: bool
    max_chars_per_file: int
    max_total_context_chars: int
    title: str
    viewpoint: str
    kind: str
    target_chars: str
    source_engine: str
    scene_count: int
    context_file_count: int
    missing_required_context_count: int
    issue_count: int
    premise_checks: list[str]
    must_do: list[str]
    must_not: list[str]
    scene_tasks: list[DraftBriefSceneTask]
    scene_plan: ScenePlanReport
    context_pack: ContextPackReport
    issues: list[DraftBriefIssue]


@dataclass
class PostDraftIssue:
    severity: str
    code: str
    path: str
    message: str


@dataclass
class PostDraftReport:
    target: str
    book: str
    chapter: str
    output_file: str | None
    dry_run: bool
    written: bool
    min_chapter_chars: int
    status: str
    ready: bool
    chapter_file: str
    engine_file: str
    retrospective_file: str
    chapter_exists: bool
    chapter_placeholder: bool
    engine_exists: bool
    engine_placeholder: bool
    retrospective_exists: bool
    retrospective_placeholder: bool
    chapter_chars: int
    chapter_nonspace_chars: int
    chapter_cjk_chars: int
    retrospective_actual_chars: str
    sync_items: list[str]
    issue_count: int
    next_actions: list[str]
    issues: list[PostDraftIssue]


@dataclass
class ReviewGateCheck:
    name: str
    source_command: str
    status: str
    issue_count: int
    blocking_issue_count: int
    summary: str


@dataclass
class ReviewGateIssue:
    severity: str
    source: str
    code: str
    subject: str
    path: str
    message: str


@dataclass
class ReviewGateReport:
    target: str
    book: str
    chapter: str
    output_file: str | None
    dry_run: bool
    written: bool
    status: str
    ready: bool
    issue_count: int
    blocking_issue_count: int
    checks: list[ReviewGateCheck]
    issues: list[ReviewGateIssue]
    next_actions: list[str]
    post_draft: PostDraftReport


@dataclass
class BookGateCheck:
    name: str
    source_command: str
    status: str
    issue_count: int
    blocking_issue_count: int
    summary: str


@dataclass
class BookGateIssue:
    severity: str
    source: str
    code: str
    subject: str
    path: str
    message: str


@dataclass
class BookGateReport:
    target: str
    book: str
    output_file: str | None
    dry_run: bool
    written: bool
    status: str
    ready: bool
    issue_count: int
    blocking_issue_count: int
    checks: list[BookGateCheck]
    issues: list[BookGateIssue]
    next_actions: list[str]
    plan: PlanAuditReport | None
    retrospective: RetrospectiveReport
    revision_plan: RevisionPlanReport
    word_scan: WordScanReport
    tables: TableCheckReport


@dataclass
class ReleaseGateCheck:
    name: str
    source_command: str
    status: str
    issue_count: int
    blocking_issue_count: int
    summary: str


@dataclass
class ReleaseGateIssue:
    severity: str
    source: str
    code: str
    subject: str
    path: str
    message: str


@dataclass
class ReleaseGateReport:
    target: str
    book: str
    output_file: str | None
    dry_run: bool
    written: bool
    status: str
    ready: bool
    issue_count: int
    blocking_issue_count: int
    checks: list[ReleaseGateCheck]
    issues: list[ReleaseGateIssue]
    next_actions: list[str]
    book_gate: BookGateReport
    publish: PublishAuditReport
    metadata: PublishMetadataReport
    manifest: PublishManifestReport
    epub: EpubAuditReport


@dataclass
class RevisionTask:
    priority: str
    area: str
    source_command: str
    code: str
    chapter: str
    path: str
    message: str
    suggested_action: str


@dataclass
class RevisionPlanReport:
    target: str
    book: str
    status: str
    output_file: str | None
    dry_run: bool
    written: bool
    task_count: int
    priority_counts: dict[str, int]
    tasks: list[RevisionTask]


@dataclass
class ReleaseEvidenceIssue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class ReleaseEvidenceReport:
    target: str
    evidence_file: str
    evidence_file_exists: bool
    status: str
    ready: bool
    decision: str
    field_count: int
    missing_required_fields: list[str]
    issue_count: int
    blocking_issue_count: int
    issues: list[ReleaseEvidenceIssue]
    next_actions: list[str]


@dataclass
class DogfoodCycleIssue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class DogfoodCycleReport:
    target: str
    evidence_file: str
    evidence_file_exists: bool
    status: str
    ready: bool
    decision: str
    field_count: int
    missing_required_fields: list[str]
    issue_count: int
    blocking_issue_count: int
    issues: list[DogfoodCycleIssue]
    next_actions: list[str]


@dataclass
class StabilityWindowIssue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class StabilityWindowReport:
    target: str
    evidence_file: str
    evidence_file_exists: bool
    status: str
    ready: bool
    decision: str
    field_count: int
    missing_required_fields: list[str]
    issue_count: int
    blocking_issue_count: int
    issues: list[StabilityWindowIssue]
    next_actions: list[str]


@dataclass
class StableCoreIssue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class StableCoreActionItem:
    item_id: str
    title: str
    status: str
    priority: str
    evidence_file: str
    audit_command: str
    acceptance: str
    notes: str


@dataclass
class StableCoreReport:
    target: str
    status: str
    ready: bool
    local_foundation_ready: bool
    release_evidence_ready: bool
    dogfood_cycle_ready: bool
    stability_window_ready: bool
    stable_core_doc_claim: str
    milestone_claim: str
    issue_count: int
    blocking_issue_count: int
    issues: list[StableCoreIssue]
    evidence: dict[str, object]
    action_items: list[StableCoreActionItem]
    next_actions: list[str]


@dataclass
class AgentPromptReport:
    target: str
    role: str
    role_name: str
    task: str
    book: str
    chapter: str | None
    output_file: str | None
    dry_run: bool
    written: bool
    include_context: bool
    prompt: str
    context_pack: ContextPackReport | None


@dataclass
class ModelConfigIssue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class ModelConfigReport:
    target: str
    config_file: str
    config_file_exists: bool
    provider: str
    planning_model: str
    drafting_model: str
    audit_model: str
    api_key_env: str
    base_url: str
    env_present: bool
    write: bool
    dry_run: bool
    written: bool
    config: dict[str, object]
    issues: list[ModelConfigIssue]


@dataclass
class AgentRunFile:
    kind: str
    path: str
    written: bool


@dataclass
class AgentConnectFile:
    kind: str
    path: str
    written: bool


@dataclass
class AgentConnectReport:
    target: str
    connector_name: str
    mode: str
    output_dir: str | None
    dry_run: bool
    written: bool
    provider: str
    model: str
    api_key_env: str
    env_present: bool
    file_count: int
    files: list[AgentConnectFile]
    manifest: dict[str, object]
    smoke_commands: list[str]
    safety: dict[str, object]
    next_actions: list[str]


@dataclass
class AgentRunReport:
    target: str
    role: str
    role_name: str
    task: str
    book: str
    chapter: str | None
    output_dir: str | None
    dry_run: bool
    written: bool
    execution_mode: str
    provider: str
    model: str
    model_config_file: str
    model_config_issue_count: int
    prompt_file: str | None
    context_pack_file: str | None
    draft_brief_file: str | None
    request_file: str | None
    readme_file: str | None
    file_count: int
    files: list[AgentRunFile]
    next_actions: list[str]
    agent_prompt: AgentPromptReport
    context_pack: ContextPackReport
    draft_brief: DraftBriefReport | None
    model_config: ModelConfigReport


@dataclass
class AgentExecReport:
    target: str
    run_dir: str
    request_file: str
    output_file: str
    receipt_file: str
    role: str
    task: str
    book: str
    chapter: str | None
    provider: str
    model: str
    command: list[str]
    timeout_seconds: int
    input_chars: int
    stdout_chars: int
    stderr_chars: int
    stderr_preview: str
    returncode: int | None
    dry_run: bool
    executed: bool
    written: bool
    safety: dict[str, object]
    next_actions: list[str]


@dataclass
class WritingAgentCommandReport:
    command: str
    target: str
    role: str
    task: str
    book: str
    chapter: str | None
    run_dir: str | None
    prepared: bool
    executed: bool
    inbox_status: str | None
    ready_count: int
    staged_outputs: list[dict[str, object]]
    stop_reason: str
    next_actions: list[str]
    agent_run: AgentRunReport
    agent_exec: AgentExecReport | None
    inbox: AgentInboxReport | None


@dataclass
class AgentSessionStep:
    stage: str
    command: str
    role: str
    task: str
    run_dir: str
    status: str
    next_command: str


@dataclass
class AgentSessionFile:
    kind: str
    path: str
    written: bool


@dataclass
class AgentSessionReport:
    target: str
    session_id: str
    goal: str
    book: str
    chapter: str | None
    output_dir: str
    dry_run: bool
    written: bool
    status: str
    step_count: int
    ready_count: int
    files: list[AgentSessionFile]
    steps: list[AgentSessionStep]
    next_actions: list[str]


@dataclass
class AgentInboxIssue:
    severity: str
    code: str
    run_dir: str
    path: str
    message: str


@dataclass
class AgentInboxRun:
    run_dir: str
    request_file: str | None
    output_file: str | None
    state: str
    role: str
    task: str
    book: str
    chapter: str | None
    output_chars: int
    issue_count: int
    issues: list[AgentInboxIssue]
    next_actions: list[str]


@dataclass
class AgentInboxReport:
    target: str
    mode: str
    runs_dir: str
    status: str
    run_count: int
    ready_count: int
    awaiting_count: int
    needs_attention_count: int
    output_name: str | None
    runs: list[AgentInboxRun]
    issues: list[AgentInboxIssue]


@dataclass
class AgentNextCandidate:
    priority: str
    stage: str
    command: str
    reason: str
    safe_to_auto_run: bool
    requires_human_review: bool


@dataclass
class AgentNextReport:
    target: str
    book: str
    chapter: str | None
    status: str
    selected_command: str
    selected_reason: str
    candidate_count: int
    candidates: list[AgentNextCandidate]
    evidence: dict[str, object]
    notes: list[str]


@dataclass
class AgentEvaluationMetric:
    name: str
    value: str
    evidence: str


@dataclass
class AgentEvaluationReport:
    target: str
    fixture_source: str
    fixture_copy: str
    book: str
    chapter: str
    runner: str
    status: str
    ready: bool
    task_ids: list[str]
    commands: list[str]
    metrics: list[AgentEvaluationMetric]
    observations: dict[str, object]
    output_file: str | None
    dry_run: bool
    written: bool
    next_actions: list[str]


@dataclass
class AgentWorkflowIssue:
    severity: str
    code: str
    field: str
    message: str


@dataclass
class AgentWorkflowReport:
    target: str
    level: str
    status: str
    ready: bool
    issue_count: int
    blocking_issue_count: int
    issues: list[AgentWorkflowIssue]
    evidence: dict[str, object]
    next_actions: list[str]


@dataclass
class AgentSmokeStep:
    name: str
    status: str
    summary: str


@dataclass
class AgentSmokeReport:
    target: str
    connector_name: str
    level: str
    status: str
    ready: bool
    run_dir: str
    adapter_file: str
    output_name: str
    dry_run: bool
    written: bool
    step_count: int
    steps: list[AgentSmokeStep]
    audit: AgentWorkflowReport
    agent_run: AgentRunReport | None
    agent_exec: AgentExecReport | None
    inbox: AgentInboxReport | None
    next_actions: list[str]


@dataclass
class DoctorReport:
    target: str
    status: str
    standard_check: str
    issue_counts: dict[str, int]
    stats: dict[str, object]
    wave: dict[str, object]
    style: dict[str, object]
    word_scan: dict[str, object]
    tables: dict[str, object]
    continuity: dict[str, object]
    characters: dict[str, object]
    echoes: dict[str, object]
    info: dict[str, object]
    plan: dict[str, object]
    retrospective: dict[str, object]
    book_gate: dict[str, object]
    agent_inbox: dict[str, object]
    model_config: dict[str, object]
    publish: dict[str, object]
    metadata: dict[str, object]
    manifest: dict[str, object]
    epub: dict[str, object]
    release_gate: dict[str, object]
    recommendations: list[str]
