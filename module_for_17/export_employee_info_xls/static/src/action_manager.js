/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { download } from "@web/core/network/download";
import { useService } from "@web/core/utils/hooks";

const { Component } = owl;


class PrintExcel extends Component {
    setup() {
        this.orm = useService("orm");
    }

    async onDownloadButtonClicked() {
        // console.log(this.env.model.root.data.project_ids.records);

        const projects = this.env.model.root.data.project_ids.records
        const employees = this.env.model.root.data.target_employees_ids.records
        
        const projects_ids = projects.map((project) =>{
            return project.data;
        })
        const target_employees_ids = employees.map((employee) =>{
            return employee.data;
        })

        const data = { "project.project": projects_ids, "hr.employee": target_employees_ids};

        console.log("Projects:", projects);
        console.log("employees:", employees);
        console.log("target_employees_ids:", target_employees_ids);
        console.log("projects_ids:", projects_ids);
        console.log("downloading excel file");

        download({
            url: '/xlsx_reports_2',
            data: { data: JSON.stringify(data) },
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }
}

PrintExcel.template = "export_employee_info_xls.PrintExcel";
PrintExcel.props = {
    ...standardWidgetProps,
};

const printExcel = {
    component: PrintExcel,
}

registry.category("view_widgets").add("custom_print_excel_file", printExcel);
