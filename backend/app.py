from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session

from models.database import init_db, get_db
from models.models import Project, Script, Display
from services.project_service import ProjectService, ScriptService, DisplayService
from services.script_execution_service import ScriptExecutionService

# 创建Flask应用
app = Flask(__name__)

# 配置CORS
CORS(app, origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"])

# 初始化数据库
init_db()


# 项目相关API
@app.route("/api/projects", methods=["GET"])
def get_projects():
    """获取所有项目列表"""
    db = next(get_db())
    try:
        projects = ProjectService.get_all_projects(db)
        return jsonify([project.__dict__ for project in projects])
    finally:
        db.close()


@app.route("/api/projects", methods=["POST"])
def create_project():
    """创建新项目"""
    data = request.json
    db = next(get_db())
    try:
        project = ProjectService.create_project(db, data)
        return jsonify(project.__dict__), 201
    finally:
        db.close()


@app.route("/api/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    """获取单个项目详情"""
    db = next(get_db())
    try:
        project = ProjectService.get_project_by_id(db, project_id)
        if project:
            return jsonify(project.__dict__)
        return jsonify({"error": "Project not found"}), 404
    finally:
        db.close()


@app.route("/api/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    """更新项目信息"""
    data = request.json
    db = next(get_db())
    try:
        project = ProjectService.update_project(db, project_id, data)
        if project:
            return jsonify(project.__dict__)
        return jsonify({"error": "Project not found"}), 404
    finally:
        db.close()


@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    """删除项目"""
    db = next(get_db())
    try:
        success = ProjectService.delete_project(db, project_id)
        if success:
            return jsonify({"message": "Project deleted successfully"})
        return jsonify({"error": "Project not found"}), 404
    finally:
        db.close()


# 脚本相关API
@app.route("/api/projects/<int:project_id>/scripts", methods=["GET"])
def get_project_scripts(project_id):
    """获取项目下的所有脚本"""
    db = next(get_db())
    try:
        scripts = ScriptService.get_scripts_by_project(db, project_id)
        return jsonify([script.__dict__ for script in scripts])
    finally:
        db.close()


@app.route("/api/scripts", methods=["POST"])
def create_script():
    """创建新脚本"""
    data = request.json
    db = next(get_db())
    try:
        script = ScriptService.create_script(db, data)
        return jsonify(script.__dict__), 201
    finally:
        db.close()


@app.route("/api/scripts/<int:script_id>", methods=["GET"])
def get_script(script_id):
    """获取单个脚本详情"""
    db = next(get_db())
    try:
        script = ScriptService.get_script_by_id(db, script_id)
        if script:
            return jsonify(script.__dict__)
        return jsonify({"error": "Script not found"}), 404
    finally:
        db.close()


@app.route("/api/scripts/<int:script_id>", methods=["PUT"])
def update_script(script_id):
    """更新脚本信息"""
    data = request.json
    db = next(get_db())
    try:
        script = ScriptService.update_script(db, script_id, data)
        if script:
            return jsonify(script.__dict__)
        return jsonify({"error": "Script not found"}), 404
    finally:
        db.close()


@app.route("/api/scripts/<int:script_id>", methods=["DELETE"])
def delete_script(script_id):
    """删除脚本"""
    db = next(get_db())
    try:
        success = ScriptService.delete_script(db, script_id)
        if success:
            return jsonify({"message": "Script deleted successfully"})
        return jsonify({"error": "Script not found"}), 404
    finally:
        db.close()


# 展示界面相关API
@app.route("/api/projects/<int:project_id>/displays", methods=["GET"])
def get_project_displays(project_id):
    """获取项目下的所有展示界面"""
    db = next(get_db())
    try:
        displays = DisplayService.get_displays_by_project(db, project_id)
        return jsonify([display.__dict__ for display in displays])
    finally:
        db.close()


@app.route("/api/displays", methods=["POST"])
def create_display():
    """创建新展示界面"""
    data = request.json
    db = next(get_db())
    try:
        display = DisplayService.create_display(db, data)
        return jsonify(display.__dict__), 201
    finally:
        db.close()


@app.route("/api/displays/<int:display_id>", methods=["GET"])
def get_display(display_id):
    """获取单个展示界面详情"""
    db = next(get_db())
    try:
        display = DisplayService.get_display_by_id(db, display_id)
        if display:
            return jsonify(display.__dict__)
        return jsonify({"error": "Display not found"}), 404
    finally:
        db.close()


@app.route("/api/displays/<int:display_id>", methods=["PUT"])
def update_display(display_id):
    """更新展示界面信息"""
    data = request.json
    db = next(get_db())
    try:
        display = DisplayService.update_display(db, display_id, data)
        if display:
            return jsonify(display.__dict__)
        return jsonify({"error": "Display not found"}), 404
    finally:
        db.close()


@app.route("/api/displays/<int:display_id>", methods=["DELETE"])
def delete_display(display_id):
    """删除展示界面"""
    db = next(get_db())
    try:
        success = DisplayService.delete_display(db, display_id)
        if success:
            return jsonify({"message": "Display deleted successfully"})
        return jsonify({"error": "Display not found"}), 404
    finally:
        db.close()


# 脚本执行API
@app.route("/api/scripts/<int:script_id>/execute", methods=["POST"])
def execute_script(script_id):
    """执行脚本"""
    data = request.json or {}
    db = next(get_db())
    try:
        # 获取脚本内容
        script = ScriptService.get_script_by_id(db, script_id)
        if not script:
            return jsonify({"error": "Script not found"}), 404
        
        # 执行脚本
        result = ScriptExecutionService.execute_script(
            script_content=script.content,
            variables=data.get("variables", {})
        )
        
        return jsonify({
            "success": True,
            "result": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        db.close()


# 测试API
@app.route("/api/test", methods=["GET"])
def test_api():
    """测试API连接"""
    return jsonify({"message": "API is working"})


if __name__ == "__main__":
    # 获取环境变量中的端口配置，默认使用5000
    import os
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(debug=True, port=port, host="0.0.0.0")