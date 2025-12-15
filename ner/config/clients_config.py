from pydantic import BaseModel, Field


class BasicClientConfig(BaseModel):
    openai_client: bool = Field(default=False)
    async_client: bool = Field(default=True)
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=10240)
    model: str = Field(default="gpt-4o")
    auth: str = Field(default="token")


class QnAConfig(BasicClientConfig):
    context_based: int = Field(default=1)
    top_p: float = Field(default=1.0)


class Qna(BaseModel):
    functional: QnAConfig = Field(default_factory=QnAConfig)
    adversarial_knowledge_based: QnAConfig = Field(default_factory=QnAConfig)
    adversarial_dynamic: QnAConfig = Field(default_factory=QnAConfig)


class GenerateConfig(BaseModel):
    qna: Qna = Field(default_factory=Qna)


class DeepTeamConfig(BasicClientConfig):
    enable: bool = Field(default=True)


class StoreConfig(BaseModel):
    type: str = Field(default="db_unity_catalog")
    insert: str = Field(
        default="INSERT INTO prp_mr_ffly_silver.bdv.redteaming_records (id, created_at, success, original_dialog, translated_dialog, strategy, type, knowledge_base_content, knowledge_base_content_index) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        description="The SQL query to insert records into the database.",
    )
    name: str = Field(
        default="redteaming_records",
        description="The name of the storage destination (e.g., table name or file name).",
    )


class TargetConfig(BaseModel):
    type: str = Field(default="stream")
    endpoint: str = Field(
        default="http://127.0.0.1:8000/api/chats/",
        description="The endpoint URL for the target service.",
    )


class KnowledgeBaseConfig(BaseModel):
    type: str = Field(default="tabular:csv")
    name: str = Field(
        default="KIT-chunks",
        description="The name of the knowledge base file.",
    )


class TranslateBaseConfig(BasicClientConfig):
    enable: bool = Field(default=True)
    type: str = Field(default="llm")


class EvaluateBaseConfig(BasicClientConfig):
    type: str = Field(default="llm")


class SummarizeBaseConfig(BasicClientConfig):
    type: str = Field(default="llm")


class ClientsConfig(BaseModel):
    generate: GenerateConfig = Field(default_factory=GenerateConfig)
    evaluate: EvaluateBaseConfig = Field(default_factory=EvaluateBaseConfig)
    translate: TranslateBaseConfig = Field(default_factory=TranslateBaseConfig)
    summarize: SummarizeBaseConfig = Field(default_factory=SummarizeBaseConfig)
    store: StoreConfig = Field(default_factory=StoreConfig)
    target: TargetConfig = Field(default_factory=TargetConfig)
    knowledgebase: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)
    deepteam: DeepTeamConfig = Field(default_factory=DeepTeamConfig)


class Settings(BaseModel):
    clients: ClientsConfig = Field(default_factory=ClientsConfig)
