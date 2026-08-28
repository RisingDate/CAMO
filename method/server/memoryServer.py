"""
    mcp记忆管理服务器
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from pydantic import BaseModel


# 记忆数据模型
class Memory(BaseModel):
    id: Optional[int] = None
    content: str
    timestamp: str
    conversation_id: str
    metadata: Dict[str, Any] = {}


class MemoryManager:
    def __init__(self, db_path: str = "memories.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def add_memory(self, memory: Memory) -> int:
        # 添加记忆
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO memories (content, timestamp, conversation_id, metadata)
            VALUES (?, ?, ?, ?)
        ''', (memory.content, memory.timestamp, memory.conversation_id,
              json.dumps(memory.metadata)))
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return memory_id

    def get_memories(self, conversation_id: str, limit: int = 10) -> List[Memory]:
        """获取对话记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, content, timestamp, conversation_id, metadata
            FROM memories 
            WHERE conversation_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (conversation_id, limit))

        memories = []
        for row in cursor.fetchall():
            memories.append(Memory(
                id=row[0],
                content=row[1],
                timestamp=row[2],
                conversation_id=row[3],
                metadata=json.loads(row[4])
            ))
        conn.close()
        return memories

    def search_memories(self, query: str, conversation_id: str = None,
                        limit: int = 5) -> List[Memory]:
        """搜索相关记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if conversation_id:
            cursor.execute('''
                SELECT id, content, timestamp, conversation_id, metadata
                FROM memories 
                WHERE conversation_id = ? AND content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (conversation_id, f'%{query}%', limit))
        else:
            cursor.execute('''
                SELECT id, content, timestamp, conversation_id, metadata
                FROM memories 
                WHERE content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', limit))

        memories = []
        for row in cursor.fetchall():
            memories.append(Memory(
                id=row[0],
                content=row[1],
                timestamp=row[2],
                conversation_id=row[3],
                metadata=json.loads(row[4])
            ))
        conn.close()
        return memories


# 创建MCP服务器
server = Server("memory-manager")

# 初始化记忆管理器
memory_manager = MemoryManager()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出可用工具"""
    return [
        types.Tool(
            name="add_memory",
            description="添加新的记忆到存储",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "记忆内容"},
                    "conversation_id": {"type": "string", "description": "对话ID"},
                    "metadata": {"type": "object", "description": "额外元数据"}
                },
                "required": ["content", "conversation_id"]
            }
        ),
        types.Tool(
            name="get_recent_memories",
            description="获取最近的记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string", "description": "对话ID"},
                    "limit": {"type": "number", "description": "返回数量限制"}
                },
                "required": ["conversation_id"]
            }
        ),
        types.Tool(
            name="search_memories",
            description="搜索相关记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "conversation_id": {"type": "string", "description": "对话ID（可选）"},
                    "limit": {"type": "number", "description": "返回数量限制"}
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    if name == "add_memory":
        memory = Memory(
            content=arguments["content"],
            timestamp=datetime.now().isoformat(),
            conversation_id=arguments["conversation_id"],
            metadata=arguments.get("metadata", {})
        )
        memory_id = memory_manager.add_memory(memory)
        return [types.TextContent(
            type="text",
            text=f"记忆已添加，ID: {memory_id}"
        )]

    elif name == "get_recent_memories":
        memories = memory_manager.get_memories(
            conversation_id=arguments["conversation_id"],
            limit=arguments.get("limit", 10)
        )
        if not memories:
            return [types.TextContent(type="text", text="没有找到相关记忆")]

        memory_texts = []
        for memory in memories:
            memory_texts.append(f"[{memory.timestamp}] {memory.content}")

        return [types.TextContent(
            type="text",
            text="最近的记忆:\n" + "\n".join(memory_texts)
        )]

    elif name == "search_memories":
        memories = memory_manager.search_memories(
            query=arguments["query"],
            conversation_id=arguments.get("conversation_id"),
            limit=arguments.get("limit", 5)
        )
        if not memories:
            return [types.TextContent(type="text", text="没有找到相关记忆")]

        memory_texts = []
        for memory in memories:
            memory_texts.append(f"[{memory.timestamp}] {memory.content}")

        return [types.TextContent(
            type="text",
            text=f"搜索 '{arguments['query']}' 的结果:\n" + "\n".join(memory_texts)
        )]

    else:
        raise ValueError(f"未知工具: {name}")


async def main():
    # 运行STDIO服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="memory-manager",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            ),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())