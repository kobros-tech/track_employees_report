/** @odoo-module **/
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";

const { Component } = owl;


class PrintExcel extends Component {
    setup() {
        this.orm = useService("orm");
    }

    async onDownloadButtonClicked() {
        // console.log(this.env.model.root);
        // console.log(this.env.model.root.data);
        // console.log(this.env.model.root.data.project_ids.records);

        const projects = this.env.model.root.data.project_ids.records
        const users = this.env.model.root.data.user_ids.records
        
        const projects_ids = projects.map((project) =>{
            return project.data;
        })
        const user_ids = projects.map((users) =>{
            return users.data;
        })

        const data = { "project.project": projects_ids, "res.users": user_ids};

        // console.log("Projects:", projects);
        // console.log("projects_ids:", projects_ids);
        // console.log("downloading excel file");

        download({
            url: '/xlsx_reports_2',
            data: { data: JSON.stringify(data) },
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }
}

PrintExcel.template = "export_employee_info_xls.PrintExcel";


registry.category("view_widgets").add("print_excel_file", PrintExcel);
